from pathlib import Path

from genblaze_core.models.enums import Modality
from genblaze_core.models.step import Step

from aarchive.local_media import LOCAL_IMAGE_MODEL, LocalLessonCardProvider
from aarchive.settings import Settings


def test_local_generation_needs_no_paid_api_key():
    settings = Settings(
        b2_bucket="bucket",
        b2_key_id="key-id",
        b2_app_key="app-key",
        generation_provider="local",
        generation_mode="generate_once",
    )
    assert settings.generation_configured is True
    assert settings.generation_can_run is True


def test_local_lesson_card_generates_a_real_png(tmp_path):
    provider = LocalLessonCardProvider(output_dir=tmp_path)
    step = Step(
        provider=provider.name,
        model=LOCAL_IMAGE_MODEL,
        prompt="Theme: After-Action Brief · Synthetic Exercise. Training topics: coordination, recovery.",
        modality=Modality.IMAGE,
        params={"width": 960, "height": 540},
    )
    completed = provider.generate(step)
    path = Path(completed.assets[0].url.removeprefix("file://"))
    assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert completed.provider_payload["local"]["renderer"] == "Pillow"
    assert completed.cost_usd == 0
