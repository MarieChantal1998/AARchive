from aarchive.models import Correction
from aarchive.search import apply_correction, format_timestamp, rank_scenes, segment_transcript
from aarchive.seed import DEMO_SCENES


def test_timestamp_formatting():
    assert format_timestamp(65.9) == "01:05"
    assert format_timestamp(3661) == "01:01:01"


def test_transcript_segmentation():
    grouped = segment_transcript([
        {"start": 0, "end": 4, "text": "first"},
        {"start": 4, "end": 9, "text": "second"},
        {"start": 9, "end": 24, "text": "third"},
    ], max_seconds=12)
    assert len(grouped) == 2
    assert grouped[0]["text"] == "first second"
    assert grouped[1]["start_timestamp"] == "00:09"


def test_search_ranking_prefers_exact_tags():
    results = rank_scenes("equipment problem followed by recovery", DEMO_SCENES)
    assert results
    assert results[0].scene.scene_id == "scene-004"
    assert "recovery" in results[0].matched_terms


def test_human_correction_precedence():
    original = DEMO_SCENES[0]
    correction = Correction(
        scene_id=original.scene_id,
        verdict="needs_correction",
        fields={"summary": "Human-confirmed staging sequence", "confidence": .99},
    )
    corrected = apply_correction(original, correction)
    assert corrected.summary == "Human-confirmed staging sequence"
    assert corrected.confidence == .99
    assert original.summary != corrected.summary

