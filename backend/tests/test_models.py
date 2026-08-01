from datetime import date

import pytest
from pydantic import ValidationError

from aarchive.models import ProjectCreate, Scene


def test_upload_metadata_validation():
    value = ProjectCreate(
        title="Warehouse drill",
        exercise_type="Evacuation",
        exercise_date=date(2026, 7, 31),
        filename="training.mp4",
        size_bytes=1024,
    )
    assert value.content_type == "video/mp4"
    with pytest.raises(ValidationError):
        ProjectCreate(
            title="x", exercise_type="y", exercise_date=date.today(), filename="x.mov",
            content_type="video/quicktime", size_bytes=0,
        )


def test_scene_timestamp_order_validation():
    with pytest.raises(ValidationError):
        Scene(
            scene_id="s", start_seconds=10, end_seconds=9,
            start_timestamp="00:10", end_timestamp="00:09", summary="invalid",
        )

