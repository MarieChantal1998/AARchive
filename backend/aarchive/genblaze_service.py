import logging
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from .models import Brief, BriefRequest, Scene
from .settings import Settings

logger = logging.getLogger(__name__)


class GenerationUnavailable(RuntimeError):
    pass


class GenerationFailed(RuntimeError):
    pass


@dataclass
class MediaRun:
    url: str
    sha256: str | None
    manifest_hash: str
    manifest_uri: str | None
    verified: bool
    run_id: str


class GenblazeBriefService:
    """Small, testable boundary around the real Genblaze 0.4.x API."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def available(self) -> bool:
        return self.settings.generation_configured

    def generate(self, request: BriefRequest, project_title: str, scenes: list[Scene]) -> Brief:
        if not self.available:
            raise GenerationUnavailable(
                "Live generation needs server-side OpenAI and Backblaze B2 credentials. The demo preview remains available."
            )
        brief_id = str(uuid4())
        title = request.title or f"After-Action Brief · {project_title}"
        narration = self._narration(title, scenes)
        cover_prompt = self._cover_prompt(title, scenes)
        try:
            image = self._run_image(request.project_id, brief_id, cover_prompt)
            audio = self._run_audio(request.project_id, brief_id, narration)
        except GenerationUnavailable:
            raise
        except Exception as exc:  # provider exceptions are intentionally normalized
            logger.exception("genblaze_generation_failed", extra={"project_id": request.project_id})
            raise GenerationFailed(
                "The media provider did not complete the brief. No success state was saved; please retry once."
            ) from exc

        hashes = [image.manifest_hash, audio.manifest_hash]
        return Brief(
            brief_id=brief_id,
            project_id=request.project_id,
            title=title,
            situation_summary=f"Selected moments from {project_title} were organized into a review-ready discussion brief.",
            what_occurred=[scene.summary for scene in scenes],
            positive_behaviors=[scene.observed_positive_behavior for scene in scenes if scene.observed_positive_behavior],
            improvement_opportunity=next(
                (scene.observed_issue for scene in scenes if scene.observed_issue),
                "Review the selected moments with the exercise team and capture a human-verified improvement opportunity.",
            ),
            discussion_questions=[
                "What information was available to the team at the start of this sequence?",
                "Which observable behavior should be repeated or adjusted in the next exercise?",
                "What evidence would confirm that the adjustment worked?",
            ],
            source_timestamps=[
                {
                    "scene_id": scene.scene_id,
                    "label": scene.summary,
                    "start_seconds": scene.start_seconds,
                    "timestamp": f"{scene.start_timestamp}–{scene.end_timestamp}",
                }
                for scene in scenes
            ],
            review_notice="Generated from selected footage observations and must be reviewed by a qualified human.",
            cover_url=image.url,
            narration_url=audio.url,
            provider="OpenAI via Genblaze",
            models=[self.settings.openai_image_model, self.settings.openai_tts_model],
            generated_at=_utcnow(),
            manifest_hash=_combined_hash(hashes),
            manifest_uri=image.manifest_uri,
            verification_status="verified" if image.verified and audio.verified else "unverified",
            provenance={
                "pipeline": "aarchive-after-action-brief",
                "image_run_id": image.run_id,
                "audio_run_id": audio.run_id,
                "image_sha256": image.sha256,
                "audio_sha256": audio.sha256,
                "image_manifest_hash": image.manifest_hash,
                "audio_manifest_hash": audio.manifest_hash,
                "storage_sink": "Backblaze B2 via Genblaze ObjectStorageSink",
            },
        )

    def _sink(self, project_id: str, brief_id: str):
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
            prefix=f"projects/{project_id}/briefs/{brief_id}/genblaze",
            key_strategy=KeyStrategy.HIERARCHICAL,
        )

    def _run_image(self, project_id: str, brief_id: str, prompt: str) -> MediaRun:
        from genblaze_core import Modality, Pipeline
        from genblaze_openai import DalleProvider

        result = (
            Pipeline("aarchive-brief-cover", project_id=project_id)
            .step(
                DalleProvider(api_key=self.settings.openai_api_key),
                model=self.settings.openai_image_model,
                prompt=prompt,
                modality=Modality.IMAGE,
                size="1536x1024",
                quality="medium",
            )
            .run(
                sink=self._sink(project_id, brief_id),
                timeout=self.settings.generation_timeout_seconds,
                max_retries=1,
            )
        )
        return _media_run(result)

    def _run_audio(self, project_id: str, brief_id: str, narration: str) -> MediaRun:
        from genblaze_core import Modality, Pipeline
        from genblaze_openai import OpenAITTSProvider

        result = (
            Pipeline("aarchive-brief-narration", project_id=project_id)
            .step(
                OpenAITTSProvider(api_key=self.settings.openai_api_key),
                model=self.settings.openai_tts_model,
                prompt=narration,
                modality=Modality.AUDIO,
                voice=self.settings.openai_tts_voice,
                response_format="mp3",
                instructions="Calm, concise professional training facilitator; neutral and observational.",
            )
            .run(
                sink=self._sink(project_id, brief_id),
                timeout=self.settings.generation_timeout_seconds,
                max_retries=1,
            )
        )
        return _media_run(result)

    @staticmethod
    def _narration(title: str, scenes: list[Scene]) -> str:
        summaries = " ".join(scene.summary for scene in scenes)
        positives = " ".join(
            scene.observed_positive_behavior for scene in scenes if scene.observed_positive_behavior
        )
        issue = next((scene.observed_issue for scene in scenes if scene.observed_issue), None)
        return (
            f"After-action brief: {title}. Situation summary. {summaries} "
            f"Observed positive behavior. {positives or 'Review the selected footage for repeatable behaviors.'} "
            f"Improvement opportunity. {issue or 'Confirm an improvement opportunity during human review.'} "
            "This briefing was generated from selected footage and must be reviewed by a qualified human."
        )

    @staticmethod
    def _cover_prompt(title: str, scenes: list[Scene]) -> str:
        topics = ", ".join(dict.fromkeys(topic for scene in scenes for topic in scene.training_topics))
        return (
            "Create a restrained professional after-action training brief cover in a dark graphite and warm amber palette. "
            "Show an abstract tabletop exercise workspace with timeline markers, transcript fragments, and coordination paths; "
            "no government seals, flags, camouflage, weapons, insignia, or identifiable people. "
            f"Theme: {title}. Training topics: {topics}. Leave generous negative space; do not render text."
        )


def _media_run(result: Any) -> MediaRun:
    asset = result.run.steps[0].assets[0]
    return MediaRun(
        url=asset.url,
        sha256=asset.sha256,
        manifest_hash=result.manifest.canonical_hash,
        manifest_uri=result.manifest.manifest_uri,
        verified=bool(result.manifest.verify()),
        run_id=result.run.run_id,
    )


def _combined_hash(hashes: list[str]) -> str:
    import hashlib

    return hashlib.sha256("|".join(hashes).encode()).hexdigest()


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)

