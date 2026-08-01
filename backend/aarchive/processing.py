import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from openai import OpenAI

from .keys import frame_key, metadata_key, source_key
from .models import ProcessingStatus, Project, Scene
from .search import segment_transcript
from .settings import Settings
from .storage import B2Store

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, settings: Settings, store: B2Store):
        self.settings = settings
        self.store = store

    def process(self, project_id: str) -> None:
        project = self.store.get_project(project_id)
        with tempfile.TemporaryDirectory(prefix="aarchive-") as temp_dir:
            work = Path(temp_dir)
            source = work / "original.mp4"
            audio = work / "extracted.wav"
            frames_dir = work / "frames"
            frames_dir.mkdir()
            try:
                self._status(project, ProcessingStatus.extracting, "Downloading source and extracting audio")
                source.write_bytes(
                    self.store.client.get_object(
                        Bucket=self.settings.b2_bucket, Key=source_key(project_id)
                    )["Body"].read()
                )
                self._ffmpeg(["-i", str(source), "-vn", "-ac", "1", "-ar", "16000", str(audio)])
                self._ffmpeg([
                    "-i", str(source), "-vf", "fps=1/12,scale=960:-2", "-q:v", "3",
                    str(frames_dir / "frame-%04d.jpg"),
                ])
                for index, path in enumerate(sorted(frames_dir.glob("*.jpg")), 1):
                    self.store.client.put_object(
                        Bucket=self.settings.b2_bucket,
                        Key=frame_key(project_id, index),
                        Body=path.read_bytes(),
                        ContentType="image/jpeg",
                    )
                self._status(project, ProcessingStatus.transcribing, "Creating timestamped transcript")
                transcript = self._transcribe(audio)
                self.store.put_json(metadata_key(project_id, "transcript"), transcript)
                self._status(project, ProcessingStatus.analyzing, "Organizing transcript into scenes")
                scenes = self._analyze(transcript)
                self.store.put_json(metadata_key(project_id, "scenes"), [scene.model_dump(mode="json") for scene in scenes])
                self._status(project, ProcessingStatus.indexing, "Writing searchable metadata")
                self.store.put_json(metadata_key(project_id, "corrections"), [])
                project.indexed_scene_count = len(scenes)
                self._status(project, ProcessingStatus.ready, "Processing complete")
            except Exception as exc:
                logger.exception("video_processing_failed", extra={"project_id": project_id})
                self._status(project, ProcessingStatus.failed, _safe_error(exc))

    def _status(self, project: Project, status: ProcessingStatus, message: str) -> None:
        project.status = status
        project.status_message = message
        self.store.put_json(metadata_key(project.project_id, "project"), project)

    def _ffmpeg(self, args: list[str]) -> None:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
            check=True,
            timeout=self.settings.processing_timeout_seconds,
            capture_output=True,
        )

    def _transcribe(self, audio: Path) -> dict[str, Any]:
        if not self.settings.openai_api_key:
            raise RuntimeError("Transcription credentials are missing; upload remains retryable")
        client = OpenAI(api_key=self.settings.openai_api_key, timeout=120, max_retries=1)
        with audio.open("rb") as handle:
            result = client.audio.transcriptions.create(
                model=self.settings.openai_transcription_model,
                file=handle,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
        return result.model_dump(mode="json")

    def _analyze(self, transcript: dict[str, Any]) -> list[Scene]:
        groups = segment_transcript(transcript.get("segments", []))
        if not groups:
            raise RuntimeError("No timestamped speech was detected")
        client = OpenAI(api_key=self.settings.openai_api_key, timeout=120, max_retries=1)
        schema = {
            "type": "object",
            "properties": {"scenes": {"type": "array", "items": {"type": "object"}}},
            "required": ["scenes"],
        }
        prompt = (
            "Convert each transcript group into conservative observable training metadata. Never infer identity, intent, "
            "violations, rankings, or performance beyond the supplied words. Return every Scene field; use arrays, null "
            "for unsupported issues/positives, and confidence 0-1. Preserve supplied timestamps exactly.\n"
            + json.dumps(groups)
        )
        response = client.responses.create(
            model=self.settings.openai_analysis_model,
            input=prompt,
            text={"format": {"type": "json_schema", "name": "scene_analysis", "schema": schema}},
        )
        parsed = json.loads(response.output_text)
        scenes: list[Scene] = []
        for index, (group, values) in enumerate(zip(groups, parsed["scenes"], strict=False), 1):
            values.update(group)
            values["scene_id"] = f"scene-{index:03d}"
            values["transcript_excerpt"] = group["text"][:500]
            scenes.append(Scene.model_validate(values))
        return scenes


def _safe_error(exc: Exception) -> str:
    text = str(exc).replace("\n", " ")[:240]
    blocked = ("key", "token", "secret", "authorization")
    if any(word in text.lower() for word in blocked):
        return "Processing failed because a required service could not authenticate. Check server configuration and retry."
    return f"Processing failed: {text or exc.__class__.__name__}"

