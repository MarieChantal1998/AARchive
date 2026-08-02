import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from .genblaze_service import GenerationFailed, GenerationUnavailable, GenblazeBriefService
from .keys import brief_key, metadata_key, source_key
from .models import (
    Brief,
    BriefRequest,
    Correction,
    ProcessingStatus,
    Project,
    ProjectCreate,
    SearchResult,
    UploadTicket,
)
from .processing import VideoProcessor
from .search import apply_correction, rank_scenes
from .seed import demo_brief
from .settings import Settings, get_settings
from .storage import B2Store, StorageUnavailable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("aarchive_api_started")
    one_shot_task = None
    if settings.nvidia_tts_one_shot_enabled:
        from .nvidia_tts_once import run_nvidia_tts_one_shot

        one_shot_task = asyncio.create_task(
            asyncio.to_thread(run_nvidia_tts_one_shot, settings),
            name="aarchive-nvidia-tts-one-shot",
        )
        application.state.nvidia_tts_one_shot_task = one_shot_task
    yield


settings = get_settings()
app = FastAPI(title="AARchive API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def get_store(config: Settings = Depends(get_settings)) -> B2Store:
    return B2Store(config)


@app.get("/health")
def health(config: Settings = Depends(get_settings), store: B2Store = Depends(get_store)) -> dict:
    return {
        "status": "ok",
        "service": "aarchive-api",
        "b2_configured": config.b2_configured,
        "b2_connected": store.connected(),
        "generation_configured": config.generation_configured,
        "generation_mode": config.generation_mode,
    }


@app.get("/api/projects", response_model=list[Project])
def projects(store: B2Store = Depends(get_store)):
    return [store.with_download_urls(project) for project in store.list_projects()]


@app.get("/api/projects/{project_id}")
def project_detail(project_id: str, store: B2Store = Depends(get_store)) -> dict:
    try:
        project = store.with_download_urls(store.get_project(project_id))
        corrections = {item.scene_id: item for item in store.get_corrections(project_id)}
        try:
            original_scenes = store.get_scenes(project_id)
        except StorageUnavailable:
            original_scenes = []
        scenes = [apply_correction(scene, corrections.get(scene.scene_id)) for scene in original_scenes]
        return {"project": project, "scenes": scenes, "corrections": list(corrections.values())}
    except StorageUnavailable as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/uploads/presign", response_model=UploadTicket, status_code=status.HTTP_201_CREATED)
def create_upload(payload: ProjectCreate, store: B2Store = Depends(get_store), config: Settings = Depends(get_settings)):
    if payload.size_bytes > config.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"MP4 exceeds the {config.max_upload_mb} MB upload limit")
    if not payload.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=415, detail="Only MP4 uploads are accepted")
    if not store.configured:
        raise HTTPException(status_code=503, detail="Backblaze B2 upload is not configured on this deployment")
    project_id = str(uuid4())
    project = Project(
        project_id=project_id,
        title=payload.title,
        exercise_type=payload.exercise_type,
        exercise_date=payload.exercise_date,
        description=payload.description,
        status=ProcessingStatus.uploading,
        status_message="Waiting for direct B2 upload",
        storage="b2",
    )
    store.put_json(metadata_key(project_id, "project"), project)
    key = source_key(project_id)
    return UploadTicket(
        project=project,
        upload_url=store.presign_upload(key, payload.content_type),
        headers={"Content-Type": payload.content_type},
        expires_in_seconds=900,
        object_key=key,
    )


@app.post("/api/projects/{project_id}/process", status_code=status.HTTP_202_ACCEPTED)
def process_project(project_id: str, tasks: BackgroundTasks, store: B2Store = Depends(get_store), config: Settings = Depends(get_settings)):
    project = store.get_project(project_id)
    if project.seeded_demo:
        raise HTTPException(status_code=400, detail="The seeded public demo is already processed")
    if not store.exists(source_key(project_id)):
        raise HTTPException(status_code=409, detail="The source MP4 is not present in B2; upload it before processing")
    tasks.add_task(VideoProcessor(config, store).process, project_id)
    return {"project_id": project_id, "status": "extracting", "message": "Processing started"}


@app.get("/api/search", response_model=list[SearchResult])
def search(
    q: str = Query(min_length=2, max_length=200),
    exercise_type: str | None = None,
    tag: str | None = None,
    store: B2Store = Depends(get_store),
):
    results: list[SearchResult] = []
    for project in store.list_projects():
        if project.status != ProcessingStatus.ready:
            continue
        if exercise_type and exercise_type.lower() not in project.exercise_type.lower():
            continue
        corrections = {item.scene_id: item for item in store.get_corrections(project.project_id)}
        scenes = [apply_correction(scene, corrections.get(scene.scene_id)) for scene in store.get_scenes(project.project_id)]
        if tag:
            scenes = [scene for scene in scenes if tag.lower() in " ".join(scene.search_tags).lower()]
        for ranked in rank_scenes(q, scenes):
            correction = corrections.get(ranked.scene.scene_id)
            results.append(
                SearchResult(
                    project_id=project.project_id,
                    video_title=project.title,
                    exercise_type=project.exercise_type,
                    exercise_date=project.exercise_date,
                    scene=ranked.scene,
                    relevance=ranked.score,
                    matched_terms=ranked.matched_terms,
                    verification_status=correction.verdict if correction else "unreviewed",
                )
            )
    return sorted(results, key=lambda result: result.relevance, reverse=True)


@app.put("/api/projects/{project_id}/scenes/{scene_id}/correction", response_model=Correction)
def save_correction(project_id: str, scene_id: str, correction: Correction, store: B2Store = Depends(get_store)):
    if scene_id != correction.scene_id:
        raise HTTPException(status_code=400, detail="Scene identifier mismatch")
    if project_id == "demo-coordinated-response" and not store.configured:
        raise HTTPException(status_code=503, detail="Corrections require configured B2 storage")
    existing = {item.scene_id: item for item in store.get_corrections(project_id)}
    existing[scene_id] = correction
    store.put_json(metadata_key(project_id, "corrections"), [item.model_dump(mode="json") for item in existing.values()])
    return correction


@app.get("/api/projects/{project_id}/briefs/{brief_id}", response_model=Brief)
def get_brief(project_id: str, brief_id: str, store: B2Store = Depends(get_store), config: Settings = Depends(get_settings)):
    if project_id == "demo-coordinated-response" and brief_id == "11111111-1111-4111-8111-111111111111":
        return demo_brief(config.demo_cover_url, config.demo_narration_url)
    try:
        brief = Brief.model_validate(store.get_json(brief_key(project_id, brief_id, "brief.json")))
        return store.with_brief_download_urls(brief)
    except StorageUnavailable as exc:
        raise HTTPException(status_code=404, detail="Brief not found") from exc


@app.post("/api/briefs", response_model=Brief, status_code=status.HTTP_201_CREATED)
def generate_brief(payload: BriefRequest, store: B2Store = Depends(get_store), config: Settings = Depends(get_settings)):
    project = store.get_project(payload.project_id)
    scene_map = {scene.scene_id: scene for scene in store.get_scenes(payload.project_id)}
    try:
        selected = [scene_map[scene_id] for scene_id in payload.scene_ids]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown scene: {exc.args[0]}") from exc
    service = GenblazeBriefService(config)
    cached_key = brief_key(payload.project_id, service.brief_id_for(payload), "brief.json")
    try:
        return store.with_brief_download_urls(Brief.model_validate(store.get_json(cached_key)))
    except StorageUnavailable:
        pass
    try:
        brief = service.generate(payload, project.title, selected)
        store.put_json(brief_key(payload.project_id, brief.brief_id, "brief.json"), brief)
        project.brief_count += 1
        store.put_json(metadata_key(payload.project_id, "project"), project)
        return store.with_brief_download_urls(brief)
    except GenerationUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except GenerationFailed as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/capabilities")
def capabilities(config: Settings = Depends(get_settings)) -> dict:
    provider_models = {
        "local": [config.local_image_model, config.local_audio_model],
        "gmicloud": [config.gmi_image_model, config.gmi_audio_model],
        "nvidia": [config.nvidia_image_model, config.nvidia_audio_model],
        "openai": [config.openai_image_model, config.openai_tts_model],
    }
    return {
        "max_upload_mb": config.max_upload_mb,
        "b2": {"configured": config.b2_configured, "bucket": config.b2_bucket or None},
        "generation": {
            "configured": config.generation_configured,
            "provider": config.generation_provider,
            "mode": config.generation_mode,
            "models": provider_models.get(config.generation_provider, []),
        },
        "processing": {
            "transcription_provider": config.transcription_provider,
            "transcription_model": config.local_whisper_model if config.transcription_provider == "local_whisper" else config.openai_transcription_model,
            "analysis_provider": config.analysis_provider,
        },
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
