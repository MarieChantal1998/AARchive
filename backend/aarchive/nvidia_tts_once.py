"""Run the single authorized NVIDIA Magpie narration and cache it in B2.

This job is deliberately separate from the public brief-generation endpoint.
Durable B2 markers prevent a Render restart from repeating either the short
validation request or the full narration request.
"""

from __future__ import annotations

import hashlib
import io
import logging
import wave
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from genblaze_core.models.manifest import parse_manifest

from .keys import brief_key
from .models import Brief
from .nvidia_compat import MAGPIE_MODEL, NvidiaHostedMagpieAudioProvider
from .settings import Settings
from .storage import B2Store

logger = logging.getLogger(__name__)

MAGPIE_VOICE = "Magpie-Multilingual.EN-US.Aria"
VALIDATION_TEXT = "AARchive validates one neural narration step through NVIDIA Magpie."
NARRATION_TEXT = (
    "After-action brief. During a synthetic evacuation exercise, the instructor explained "
    "the route. A human-verified simulated radio battery issue was followed by backup-radio "
    "recovery. The team then showed effective coordination during review. This brief was "
    "generated from selected footage and must be reviewed by a qualified human."
)
NVIDIA_HOSTED_TEXT_LIMIT = 350


@dataclass(frozen=True)
class TtsRunEvidence:
    run_id: str
    audio_url: str
    audio_key: str
    audio_sha256: str
    duration_seconds: float
    manifest_uri: str
    manifest_key: str
    manifest_hash: str
    manifest_verified: bool


class NvidiaTtsOneShotJob:
    """Execute at most one validation synthesis and one full synthesis."""

    def __init__(self, settings: Settings, store: B2Store | None = None):
        self.settings = settings
        self.store = store or B2Store(settings)
        self.project_id = settings.nvidia_tts_one_shot_project_id
        self.brief_id = settings.nvidia_tts_one_shot_brief_id
        self.control_prefix = (
            f"projects/{self.project_id}/briefs/{self.brief_id}/nvidia-tts-one-shot"
        )

    def run(self) -> None:
        self._validate_configuration()
        if self.store.exists(self._marker("completed")):
            logger.info("nvidia_tts_one_shot_already_completed")
            return
        if self.store.exists(self._marker("validation-started")):
            logger.warning("nvidia_tts_validation_already_attempted_no_retry")
            return

        self._put_marker("validation-started", {"status": "started"})
        try:
            validation_run_id = self._run_validation()
        except Exception as exc:
            self._put_marker(
                "validation-failed",
                {"status": "failed", "error_type": type(exc).__name__},
            )
            logger.exception("nvidia_tts_validation_failed_no_full_call")
            return
        self._put_marker(
            "validation-succeeded",
            {"status": "succeeded", "run_id": validation_run_id},
        )

        if self.store.exists(self._marker("full-started")):
            logger.warning("nvidia_tts_full_already_attempted_no_retry")
            return
        self._put_marker("full-started", {"status": "started"})
        try:
            evidence = self._run_full()
            self._promote_verified_narration(evidence, validation_run_id)
        except Exception as exc:
            self._put_marker(
                "full-failed",
                {"status": "failed", "error_type": type(exc).__name__},
            )
            logger.exception("nvidia_tts_full_failed_no_retry")
            return

        self._put_marker(
            "completed",
            {
                "status": "succeeded",
                "provider": "NVIDIA",
                "model": MAGPIE_MODEL,
                "voice": MAGPIE_VOICE,
                "hosted": True,
                "cost_usd": 0,
                "run_id": evidence.run_id,
                "audio_key": evidence.audio_key,
                "audio_sha256": evidence.audio_sha256,
                "duration_seconds": evidence.duration_seconds,
                "manifest_key": evidence.manifest_key,
                "manifest_hash": evidence.manifest_hash,
                "manifest_verified": evidence.manifest_verified,
            },
        )
        logger.info(
            "nvidia_tts_one_shot_completed run_id=%s audio_key=%s manifest_key=%s",
            evidence.run_id,
            evidence.audio_key,
            evidence.manifest_key,
        )

    def _validate_configuration(self) -> None:
        if not self.settings.nvidia_api_key:
            raise RuntimeError("NVIDIA_API_KEY is not configured")
        if not self.store.connected():
            raise RuntimeError("Backblaze B2 is not connected")
        if len(NARRATION_TEXT) > NVIDIA_HOSTED_TEXT_LIMIT:
            raise RuntimeError("NVIDIA narration exceeds the hosted endpoint character limit")
        if not self.store.exists(brief_key(self.project_id, self.brief_id, "brief.json")):
            raise RuntimeError("Target cached brief does not exist")

    def _provider(self, output_dir: Path) -> NvidiaHostedMagpieAudioProvider:
        return NvidiaHostedMagpieAudioProvider(
            api_key=self.settings.nvidia_api_key,
            output_dir=output_dir,
            synthesize_url=self.settings.nvidia_tts_synthesize_url,
            voices_url=self.settings.nvidia_tts_voices_url,
            http_timeout=self.settings.nvidia_http_timeout_seconds,
        )

    @staticmethod
    def _step_params() -> dict[str, Any]:
        return {
            "language": "en-US",
            "voice": MAGPIE_VOICE,
            "encoding": "LINEAR_PCM",
            "sample_rate_hz": 44100,
        }

    def _run_validation(self) -> str:
        from genblaze_core import Modality, Pipeline

        with TemporaryDirectory(prefix="aarchive-nvidia-validation-") as temp_dir:
            provider = self._provider(Path(temp_dir))
            try:
                pipeline = (
                    Pipeline("aarchive-nvidia-magpie-validation", project_id=self.project_id)
                    .preflight(True)
                    .step(
                        provider,
                        model=MAGPIE_MODEL,
                        prompt=VALIDATION_TEXT,
                        modality=Modality.AUDIO,
                        **self._step_params(),
                    )
                )
                completed = pipeline.run(
                    timeout=min(self.settings.nvidia_http_timeout_seconds, 180),
                    pipeline_timeout=min(self.settings.generation_timeout_seconds, 240),
                    max_retries=0,
                )
            finally:
                provider.close()
        step = completed.run.steps[0]
        if not step.assets or not step.assets[0].url:
            raise RuntimeError("NVIDIA validation returned no audio asset")
        return completed.run.run_id

    def _sink(self):
        from genblaze_core import KeyStrategy, ObjectStorageSink
        from genblaze_s3 import S3StorageBackend

        backend = S3StorageBackend.for_backblaze(
            self.settings.b2_bucket,
            region=self.settings.b2_region,
            key_id=self.settings.b2_key_id,
            app_key=self.settings.b2_app_key,
            public_url_base=self.settings.b2_public_url_base or None,
            auto_lifecycle=False,
        )
        return ObjectStorageSink(
            backend,
            prefix=(
                f"projects/{self.project_id}/briefs/{self.brief_id}/"
                "genblaze-nvidia-narration"
            ),
            key_strategy=KeyStrategy.HIERARCHICAL,
        )

    def _run_full(self) -> TtsRunEvidence:
        from genblaze_core import Modality, Pipeline

        with TemporaryDirectory(prefix="aarchive-nvidia-full-") as temp_dir:
            provider = self._provider(Path(temp_dir))
            try:
                pipeline = Pipeline(
                    "aarchive-nvidia-magpie-narration", project_id=self.project_id
                ).step(
                    provider,
                    model=MAGPIE_MODEL,
                    prompt=NARRATION_TEXT,
                    modality=Modality.AUDIO,
                    **self._step_params(),
                )
                completed = pipeline.run(
                    sink=self._sink(),
                    timeout=self.settings.nvidia_http_timeout_seconds,
                    pipeline_timeout=self.settings.generation_timeout_seconds,
                    max_retries=0,
                )
            finally:
                provider.close()

        if len(completed.run.steps) != 1 or not completed.run.steps[0].assets:
            raise RuntimeError("NVIDIA full narration returned no audio asset")
        asset = completed.run.steps[0].assets[0]
        audio_key = self.store._key_from_storage_url(asset.url)
        manifest_key = self.store._key_from_storage_url(completed.manifest.manifest_uri)
        if not audio_key or not manifest_key:
            raise RuntimeError("Genblaze did not persist durable B2 audio and manifest paths")

        audio_bytes = self.store.client.get_object(
            Bucket=self.settings.b2_bucket, Key=audio_key
        )["Body"].read()
        audio_sha256 = hashlib.sha256(audio_bytes).hexdigest()
        if asset.sha256 != audio_sha256:
            raise RuntimeError("B2 narration hash does not match the Genblaze asset hash")
        duration_seconds = self._wav_duration(audio_bytes)

        manifest_json = self.store.get_json(manifest_key)
        manifest = parse_manifest(manifest_json)
        manifest_verified = bool(manifest.verify())
        if not manifest_verified or manifest.canonical_hash != completed.manifest.canonical_hash:
            raise RuntimeError("The B2 provenance manifest did not verify canonically")

        return TtsRunEvidence(
            run_id=completed.run.run_id,
            audio_url=asset.url,
            audio_key=audio_key,
            audio_sha256=audio_sha256,
            duration_seconds=duration_seconds,
            manifest_uri=completed.manifest.manifest_uri,
            manifest_key=manifest_key,
            manifest_hash=manifest.canonical_hash,
            manifest_verified=manifest_verified,
        )

    def _promote_verified_narration(
        self, evidence: TtsRunEvidence, validation_run_id: str
    ) -> None:
        current_key = brief_key(self.project_id, self.brief_id, "brief.json")
        fallback_key = brief_key(self.project_id, self.brief_id, "brief.local-fallback.json")
        current_json = self.store.get_json(current_key)
        current = Brief.model_validate(current_json)
        if not self.store.exists(fallback_key):
            self.store.put_json(fallback_key, current_json)

        previous = dict(current.provenance)
        current.narration_url = evidence.audio_url
        current.provider = "NVIDIA neural TTS through Genblaze (Pillow cover retained)"
        current.models = ["pillow-lesson-card-v1", MAGPIE_MODEL]
        current.generated_at = datetime.now(timezone.utc)
        current.manifest_hash = evidence.manifest_hash
        current.manifest_uri = evidence.manifest_uri
        current.verification_status = "verified"
        current.provenance = {
            "pipeline": "aarchive-nvidia-magpie-narration",
            "run_id": evidence.run_id,
            "validation_run_id": validation_run_id,
            "provider": "nvidia",
            "provider_display": "NVIDIA",
            "hosted": True,
            "cost_usd": 0,
            "image_model": "pillow-lesson-card-v1",
            "audio_model": MAGPIE_MODEL,
            "audio_voice": MAGPIE_VOICE,
            "image_sha256": previous.get("image_sha256"),
            "audio_sha256": evidence.audio_sha256,
            "audio_duration_seconds": evidence.duration_seconds,
            "manifest_hash": evidence.manifest_hash,
            "storage_sink": "Backblaze B2 via Genblaze ObjectStorageSink",
            "generation_mode": "generated_once_then_cached",
            "cover_provenance": {
                "provider": previous.get("provider"),
                "model": previous.get("image_model"),
                "run_id": previous.get("run_id"),
                "manifest_hash": previous.get("manifest_hash"),
            },
            "replaced_narration": {
                "provider": previous.get("provider"),
                "model": previous.get("audio_model"),
                "sha256": previous.get("audio_sha256"),
            },
        }
        self.store.put_json(current_key, current)

    @staticmethod
    def _wav_duration(audio_bytes: bytes) -> float:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            if frame_rate <= 0:
                raise RuntimeError("NVIDIA WAV has an invalid sample rate")
            return round(wav_file.getnframes() / frame_rate, 2)

    def _marker(self, name: str) -> str:
        return f"{self.control_prefix}/{name}.json"

    def _put_marker(self, name: str, payload: dict[str, Any]) -> None:
        self.store.put_json(
            self._marker(name),
            {**payload, "updated_at": datetime.now(timezone.utc).isoformat()},
        )


def run_nvidia_tts_one_shot(settings: Settings) -> None:
    """Lifespan entry point used only when the explicit one-shot flag is set."""

    NvidiaTtsOneShotJob(settings).run()
