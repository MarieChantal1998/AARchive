import pytest

from aarchive.keys import audio_key, brief_key, frame_key, metadata_key, source_key


def test_b2_object_key_layout():
    project = "test-project"
    brief = "11111111-1111-4111-8111-111111111111"
    assert source_key(project) == "projects/test-project/source/original.mp4"
    assert audio_key(project) == "projects/test-project/audio/extracted.wav"
    assert metadata_key(project, "scenes") == "projects/test-project/metadata/scenes.json"
    assert frame_key(project, 3) == "projects/test-project/frames/frame-0003.jpg"
    assert brief_key(project, brief, "manifest.json").endswith(f"briefs/{brief}/manifest.json")


def test_key_validation_rejects_traversal():
    with pytest.raises(ValueError):
        source_key("../escape")
    with pytest.raises(ValueError):
        metadata_key("project", "secrets")
