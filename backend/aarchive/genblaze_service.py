import logging
from dataclasses import dataclass
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .generation_providers import ProviderConfigurationError, provider_for
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
    """Provider-neutral boundary around a real Genblaze Pipeline and B2 sink."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def available(self) -> bool:
        return self.settings.generation_can_run

    @staticmethod
    def brief_id_for(request: BriefRequest) -> str:
        scene_key = ",".join(sorted(request.scene_ids))
        return str(uuid5(NAMESPACE_URL, f"aarchive:v1:{request.project_id}:{scene_key}"))

    def generate(self, request: BriefRequest, project_title: str, scenes: list[Scene]) -> Brief:
        if not self.available:
            if self.settings.generation_mode != "generate_once":
                raise GenerationUnavailable(
                    "Public generation is cached-only. A previously generated B2 brief is returned when available."
                )
            raise GenerationUnavailable(
                f"{self.settings.generation_provider} generation needs a server-side provider key and Backblaze B2 credentials."
            )
        brief_id = self.brief_id_for(request)
        title = request.title or f"After-Action Brief · {project_title}"
        narration = self._narration(title, scenes)
        cover_prompt = self._cover_prompt(title, scenes)
        try:
            provider = provider_for(self.settings)
            image, audio, manifest_hash, manifest_uri, verified, run_id = self._run_pipeline(
                request.project_id, brief_id, cover_prompt, narration, provider
            )
        except ProviderConfigurationError as exc:
            raise GenerationUnavailable(str(exc)) from exc
        except Exception as exc:  # provider exceptions are intentionally normalized
            logger.exception("genblaze_generation_failed", extra={"project_id": request.project_id})
            raise GenerationFailed(
                "The media provider did not complete the one-time demo run. No success state was saved."
            ) from exc

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
            provider=provider.display_name,
            models=[provider.image_model, provider.audio_model],
            generated_at=_utcnow(),
            manifest_hash=manifest_hash,
            manifest_uri=manifest_uri,
            verification_status="verified" if verified else "unverified",
            provenance={
                "pipeline": "aarchive-after-action-brief",
                "run_id": run_id,
                "provider": provider.slug,
                "image_model": provider.image_model,
                "audio_model": provider.audio_model,
                "image_sha256": image.sha256,
                "audio_sha256": audio.sha256,
                "manifest_hash": manifest_hash,
                "storage_sink": "Backblaze B2 via Genblaze ObjectStorageSink",
                "generation_mode": "generated_once_then_cached",
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

    def _run_pipeline(self, project_id: str, brief_id: str, cover_prompt: str, narration: str, provider):
        from genblaze_core import Modality, Pipeline

        result = (
            Pipeline("aarchive-after-action-brief", project_id=project_id)
            .step(
                provider.image_factory(),
                model=provider.image_model,
                prompt=cover_prompt,
                modality=Modality.IMAGE,
                **provider.image_params,
            )
            .step(
                provider.audio_factory(),
                model=provider.audio_model,
                prompt=narration,
                modality=Modality.AUDIO,
                **provider.audio_params,
            )
        )
        completed = result.run(
            sink=self._sink(project_id, brief_id),
            timeout=self.settings.generation_timeout_seconds,
            max_retries=1,
        )
        if len(completed.run.steps) != 2:
            raise GenerationFailed("Genblaze did not return both required media steps")
        image = _asset_run(completed.run.steps[0].assets[0])
        audio = _asset_run(completed.run.steps[1].assets[0])
        return (
            image,
            audio,
            completed.manifest.canonical_hash,
            completed.manifest.manifest_uri,
            bool(completed.manifest.verify()),
            completed.run.run_id,
        )

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


def _asset_run(asset: Any) -> MediaRun:
    return MediaRun(
        url=asset.url,
        sha256=asset.sha256,
        manifest_hash="",
        manifest_uri=None,
        verified=False,
        run_id="",
    )


def _utcnow():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc)
