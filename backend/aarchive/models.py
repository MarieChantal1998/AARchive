from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ProcessingStatus(StrEnum):
    uploading = "uploading"
    extracting = "extracting"
    transcribing = "transcribing"
    analyzing = "analyzing_scenes"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"


class Scene(BaseModel):
    scene_id: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(gt=0)
    start_timestamp: str
    end_timestamp: str
    summary: str
    transcript_excerpt: str = ""
    people_or_roles: list[str] = []
    activities: list[str] = []
    equipment: list[str] = []
    location_or_environment: list[str] = []
    training_topics: list[str] = []
    observed_issue: str | None = None
    observed_positive_behavior: str | None = None
    search_tags: list[str] = []
    confidence: float = Field(default=0.5, ge=0, le=1)
    observation_notice: str = "Machine-generated observation; human verification required."

    @field_validator("end_seconds")
    @classmethod
    def end_after_start(cls, value: float, info: Any) -> float:
        start = info.data.get("start_seconds", 0)
        if value <= start:
            raise ValueError("end_seconds must be greater than start_seconds")
        return value


class Correction(BaseModel):
    scene_id: str
    verdict: Literal["accurate", "needs_correction"]
    fields: dict[str, Any] = {}
    corrected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    exercise_type: str = Field(min_length=2, max_length=80)
    exercise_date: date
    description: str | None = Field(default=None, max_length=1000)
    filename: str = Field(min_length=1, max_length=255)
    content_type: Literal["video/mp4"] = "video/mp4"
    size_bytes: int = Field(gt=0)


class Project(BaseModel):
    project_id: str
    title: str
    exercise_type: str
    exercise_date: date
    description: str | None = None
    duration_seconds: float = 0
    status: ProcessingStatus
    status_message: str = ""
    thumbnail_url: str | None = None
    video_url: str | None = None
    indexed_scene_count: int = 0
    brief_count: int = 0
    storage: Literal["b2", "public_demo"] = "b2"
    seeded_demo: bool = False
    source_attribution: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchResult(BaseModel):
    project_id: str
    video_title: str
    exercise_type: str
    exercise_date: date
    scene: Scene
    relevance: float
    matched_terms: list[str]
    verification_status: str


class BriefRequest(BaseModel):
    project_id: str
    scene_ids: list[str] = Field(min_length=1, max_length=12)
    title: str | None = Field(default=None, max_length=140)


class Brief(BaseModel):
    brief_id: str
    project_id: str
    title: str
    situation_summary: str
    what_occurred: list[str]
    positive_behaviors: list[str]
    improvement_opportunity: str
    discussion_questions: list[str]
    source_timestamps: list[dict[str, Any]]
    review_notice: str
    cover_url: str | None = None
    narration_url: str | None = None
    provider: str
    models: list[str]
    generated_at: datetime
    manifest_hash: str | None = None
    manifest_uri: str | None = None
    verification_status: Literal["verified", "unverified", "not_generated"]
    provenance: dict[str, Any] = {}
    seeded_demo: bool = False


class UploadTicket(BaseModel):
    project: Project
    upload_url: str
    method: Literal["PUT"] = "PUT"
    headers: dict[str, str]
    expires_in_seconds: int
    object_key: str

