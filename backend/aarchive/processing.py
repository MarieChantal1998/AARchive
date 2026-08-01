import json
import logging
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .keys import audio_key, frame_key, metadata_key, source_key
from .models import ProcessingStatus, Project, Scene
from .search import format_timestamp, segment_transcript
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
                self.store.client.put_object(
                    Bucket=self.settings.b2_bucket,
                    Key=audio_key(project_id),
                    Body=audio.read_bytes(),
                    ContentType="audio/wav",
                )
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
                project.duration_seconds = float(transcript.get("duration") or self._duration(source))
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
        try:
            events = self.store.get_json(metadata_key(project.project_id, "processing-log"))
        except Exception:
            events = []
        events.append({
            "status": status.value,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.store.put_json(metadata_key(project.project_id, "processing-log"), events)

    def _ffmpeg(self, args: list[str]) -> None:
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args],
            check=True,
            timeout=self.settings.processing_timeout_seconds,
            capture_output=True,
        )

    def _transcribe(self, audio: Path) -> dict[str, Any]:
        if self.settings.transcription_provider == "local_whisper":
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError("Local Whisper is not installed; processing remains retryable") from exc
            model = WhisperModel(
                self.settings.local_whisper_model,
                device="cpu",
                compute_type="int8",
                cpu_threads=2,
            )
            generated, info = model.transcribe(
                str(audio),
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            segments = [
                {"id": index, "start": item.start, "end": item.end, "text": item.text.strip()}
                for index, item in enumerate(generated)
                if item.text.strip()
            ]
            return {
                "provider": "local_whisper",
                "model": self.settings.local_whisper_model,
                "language": info.language,
                "duration": info.duration,
                "text": " ".join(item["text"] for item in segments),
                "segments": segments,
            }
        if self.settings.transcription_provider == "openai":
            if not self.settings.openai_api_key:
                raise RuntimeError("Optional OpenAI transcription is selected but has no funded API key")
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key, timeout=120, max_retries=1)
            with audio.open("rb") as handle:
                result = client.audio.transcriptions.create(
                    model=self.settings.openai_transcription_model,
                    file=handle,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            return result.model_dump(mode="json")
        raise RuntimeError(f"Unsupported transcription provider: {self.settings.transcription_provider}")

    def _analyze(self, transcript: dict[str, Any]) -> list[Scene]:
        groups = segment_transcript(transcript.get("segments", []))
        if not groups:
            raise RuntimeError("No timestamped speech was detected")
        if self.settings.analysis_provider == "local":
            return scenes_from_groups(groups)
        if self.settings.analysis_provider != "openai":
            raise RuntimeError(f"Unsupported scene-analysis provider: {self.settings.analysis_provider}")
        if not self.settings.openai_api_key:
            raise RuntimeError("Optional OpenAI analysis is selected but has no funded API key")
        from openai import OpenAI

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

    def _duration(self, source: Path) -> float:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(source),
            ],
            check=True,
            timeout=30,
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())


def scenes_from_groups(groups: list[dict[str, Any]]) -> list[Scene]:
    """Create conservative searchable metadata without a paid model call."""
    scenes: list[Scene] = []
    for index, group in enumerate(groups, 1):
        text = str(group.get("text", "")).strip()
        lowered = text.lower()
        roles = _matches(lowered, {
            "instructor": "Instructor", "team": "Exercise team", "leader": "Team leader",
            "dispatcher": "Dispatcher", "responder": "Responder",
        })
        activities = _matches(lowered, {
            "brief": "Briefing", "evacuat": "Evacuation", "communicat": "Communication",
            "radio": "Radio communication", "recover": "Recovery", "coordinate": "Coordination",
            "review": "After-action review", "confirm": "Confirmation",
        })
        equipment = _matches(lowered, {
            "radio": "Radio", "battery": "Radio battery", "medical": "Medical equipment",
            "stretcher": "Stretcher", "vehicle": "Vehicle",
        })
        environments = _matches(lowered, {
            "warehouse": "Warehouse training area", "evacuation point": "Evacuation point",
            "briefing area": "Briefing area", "vehicle area": "Vehicle area",
        })
        topics = list(dict.fromkeys(activities + _matches(lowered, {
            "procedure": "Emergency procedure", "handoff": "Handoff", "equipment": "Equipment use",
            "emergency": "Emergency response", "route": "Route management",
        })))
        issue = None
        if re.search(r"\b(problem|breakdown|interrupt|failed|failure|delay|lost|unclear)\b", lowered):
            issue = "The transcript records a simulated interruption or problem that requires human verification."
        positive = None
        if re.search(r"\b(recover|coordinate|confirm|repeat|resume|clear|effective)\w*\b", lowered):
            positive = "The transcript records a recovery or coordination behavior that requires human verification."
        tags = sorted(set(
            re.findall(r"[a-z0-9]+", lowered)
            + [item.lower() for item in activities + equipment + topics]
        ))
        summary = text if len(text) <= 180 else f"{text[:177].rstrip()}..."
        scenes.append(Scene(
            scene_id=f"scene-{index:03d}",
            start_seconds=float(group["start_seconds"]),
            end_seconds=float(group["end_seconds"]),
            start_timestamp=str(group.get("start_timestamp") or format_timestamp(float(group["start_seconds"]))),
            end_timestamp=str(group.get("end_timestamp") or format_timestamp(float(group["end_seconds"]))),
            summary=summary,
            transcript_excerpt=text[:500],
            people_or_roles=roles,
            activities=activities,
            equipment=equipment,
            location_or_environment=environments,
            training_topics=topics,
            observed_issue=issue,
            observed_positive_behavior=positive,
            search_tags=tags,
            confidence=0.72,
        ))
    return scenes


def _matches(text: str, mapping: dict[str, str]) -> list[str]:
    return [label for needle, label in mapping.items() if needle in text]


def _safe_error(exc: Exception) -> str:
    text = str(exc).replace("\n", " ")[:240]
    blocked = ("key", "token", "secret", "authorization")
    if any(word in text.lower() for word in blocked):
        return "Processing failed because a required service could not authenticate. Check server configuration and retry."
    return f"Processing failed: {text or exc.__class__.__name__}"
