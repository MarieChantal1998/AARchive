from fastapi.testclient import TestClient

from aarchive.main import app

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
    assert "secret" not in payload.lower()

