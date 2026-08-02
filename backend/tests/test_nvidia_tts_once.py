from aarchive.nvidia_compat import MAGPIE_MODEL
from aarchive.nvidia_tts_once import (
    NVIDIA_HOSTED_TEXT_LIMIT,
    NARRATION_TEXT,
    VALIDATION_TEXT,
    NvidiaTtsOneShotJob,
    TtsRunEvidence,
)
from aarchive.settings import Settings


class FakeStore:
    def __init__(self, existing: set[str] | None = None):
        self.existing = existing or set()
        self.writes: list[tuple[str, dict]] = []

    def exists(self, key: str) -> bool:
        return key in self.existing

    def put_json(self, key: str, value: dict) -> None:
        self.writes.append((key, value))
        self.existing.add(key)


def make_job(store: FakeStore) -> NvidiaTtsOneShotJob:
    settings = Settings(nvidia_api_key="test-key")
    return NvidiaTtsOneShotJob(settings, store=store)  # type: ignore[arg-type]


def test_nvidia_narration_respects_hosted_limit_and_identifies_review_requirement():
    assert len(VALIDATION_TEXT) < len(NARRATION_TEXT)
    assert len(NARRATION_TEXT) <= NVIDIA_HOSTED_TEXT_LIMIT
    assert "synthetic evacuation exercise" in NARRATION_TEXT
    assert "must be reviewed by a qualified human" in NARRATION_TEXT


def test_completed_marker_prevents_any_provider_call(monkeypatch):
    store = FakeStore()
    job = make_job(store)
    store.existing.add(job._marker("completed"))
    monkeypatch.setattr(job, "_validate_configuration", lambda: None)
    monkeypatch.setattr(
        job,
        "_run_validation",
        lambda: (_ for _ in ()).throw(AssertionError("validation must not run")),
    )

    job.run()

    assert store.writes == []


def test_success_path_records_bounded_calls_and_verified_evidence(monkeypatch):
    store = FakeStore()
    job = make_job(store)
    evidence = TtsRunEvidence(
        run_id="full-run",
        audio_url="https://example.test/projects/audio.wav",
        audio_key="projects/p/briefs/b/audio.wav",
        audio_sha256="a" * 64,
        duration_seconds=22.5,
        manifest_uri="https://example.test/projects/manifest.json",
        manifest_key="projects/p/briefs/b/manifest.json",
        manifest_hash="b" * 64,
        manifest_verified=True,
    )
    promoted: list[tuple[TtsRunEvidence, str]] = []
    monkeypatch.setattr(job, "_validate_configuration", lambda: None)
    monkeypatch.setattr(job, "_run_validation", lambda: "validation-run")
    monkeypatch.setattr(job, "_run_full", lambda: evidence)
    monkeypatch.setattr(job, "_promote_verified_narration", lambda value, run: promoted.append((value, run)))

    job.run()

    written_names = [key.rsplit("/", 1)[-1] for key, _ in store.writes]
    assert written_names == [
        "validation-started.json",
        "validation-succeeded.json",
        "full-started.json",
        "completed.json",
    ]
    assert promoted == [(evidence, "validation-run")]
    completed = store.writes[-1][1]
    assert completed["provider"] == "NVIDIA"
    assert completed["model"] == MAGPIE_MODEL
    assert completed["cost_usd"] == 0
