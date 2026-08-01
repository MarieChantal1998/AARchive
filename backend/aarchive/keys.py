from uuid import UUID


def project_prefix(project_id: str) -> str:
    if not project_id or "/" in project_id or ".." in project_id:
        raise ValueError("invalid project id")
    return f"projects/{project_id}"


def source_key(project_id: str) -> str:
    return f"{project_prefix(project_id)}/source/original.mp4"


def audio_key(project_id: str) -> str:
    return f"{project_prefix(project_id)}/audio/extracted.wav"


def metadata_key(project_id: str, name: str) -> str:
    allowed = {"project", "transcript", "scenes", "corrections", "processing-log"}
    if name not in allowed:
        raise ValueError("unsupported metadata object")
    return f"{project_prefix(project_id)}/metadata/{name}.json"


def frame_key(project_id: str, index: int) -> str:
    if index < 1:
        raise ValueError("frame index must be positive")
    return f"{project_prefix(project_id)}/frames/frame-{index:04d}.jpg"


def brief_key(project_id: str, brief_id: str, name: str) -> str:
    UUID(brief_id)
    if name not in {"brief.json", "cover.png", "narration.mp3", "manifest.json"}:
        raise ValueError("unsupported brief object")
    return f"{project_prefix(project_id)}/briefs/{brief_id}/{name}"
