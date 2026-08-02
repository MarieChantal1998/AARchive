from fastapi.testclient import TestClient

from aarchive.main import app
from aarchive.settings import Settings, get_settings

app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
client = TestClient(app)


def test_health_and_seeded_library():
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    projects = client.get("/api/projects")
    assert projects.status_code == 200
    assert projects.json()[0]["seeded_demo"] is True


def test_failed_upload_state_is_explicit_when_b2_missing():
    response = client.post("/api/uploads/presign", json={
        "title": "Synthetic drill",
        "exercise_type": "Evacuation",
        "exercise_date": "2026-07-31",
        "filename": "drill.mp4",
        "content_type": "video/mp4",
        "size_bytes": 1024,
    })
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


def test_api_never_returns_credentials():
    payload = str(client.get("/api/capabilities").json()) + str(client.get("/health").json())
    assert "B2_APP_KEY" not in payload
    assert "OPENAI_API_KEY" not in payload
    assert "GMI_API_KEY" not in payload
    assert "NVIDIA_API_KEY" not in payload
    assert "secret" not in payload.lower()


def test_private_brief_assets_are_presigned_without_changing_durable_record():
    from aarchive.models import Brief
    from aarchive.storage import B2Store

    class FakeClient:
        def generate_presigned_url(self, operation, Params, ExpiresIn):
            return f"https://signed.example/{Params['Key']}?expires={ExpiresIn}"

    settings = Settings(b2_bucket="bucket", b2_key_id="id", b2_app_key="secret")
    store = B2Store(settings)
    store._client = FakeClient()
    durable = Brief.model_validate(
        {
            "brief_id": "8eb28934-d786-5dc2-b134-12dc027e3d23",
            "project_id": "project",
            "title": "Brief",
            "situation_summary": "Summary",
            "what_occurred": [],
            "positive_behaviors": [],
            "improvement_opportunity": "Review",
            "discussion_questions": [],
            "source_timestamps": [],
            "review_notice": "Review required",
            "cover_url": "https://s3.example/bucket/projects/project/briefs/id/cover.png",
            "narration_url": "https://s3.example/bucket/projects/project/briefs/id/narration.mp3",
            "provider": "local",
            "models": ["image", "audio"],
            "generated_at": "2026-08-02T00:00:00Z",
            "manifest_uri": "https://s3.example/bucket/projects/project/briefs/id/manifest.json",
            "verification_status": "verified",
        }
    )
    hydrated = store.with_brief_download_urls(durable)
    assert hydrated.cover_url.startswith("https://signed.example/projects/")
    assert hydrated.narration_url.startswith("https://signed.example/projects/")
    assert hydrated.manifest_uri.startswith("https://signed.example/projects/")
    assert durable.cover_url.startswith("https://s3.example/bucket/")
