import re
from dataclasses import dataclass
from typing import Any

from .models import Correction, Scene

TOKEN_RE = re.compile(r"[a-z0-9]+")


def format_timestamp(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def apply_correction(scene: Scene, correction: Correction | None) -> Scene:
    if not correction or not correction.fields:
        return scene.model_copy(deep=True)
    allowed = set(Scene.model_fields) - {"scene_id", "start_seconds", "end_seconds"}
    updates = {key: value for key, value in correction.fields.items() if key in allowed}
    return scene.model_copy(update=updates, deep=True)


def _flatten(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value or "")


@dataclass
class RankedScene:
    scene: Scene
    score: float
    matched_terms: list[str]


def rank_scenes(query: str, scenes: list[Scene]) -> list[RankedScene]:
    terms = list(dict.fromkeys(TOKEN_RE.findall(query.lower())))
    if not terms:
        return []
    ranked: list[RankedScene] = []
    for scene in scenes:
        fields = {
            "summary": scene.summary,
            "transcript": scene.transcript_excerpt,
            "tags": _flatten(scene.search_tags),
            "topics": _flatten(scene.training_topics),
            "activities": _flatten(scene.activities),
            "positive": scene.observed_positive_behavior,
            "issue": scene.observed_issue,
        }
        haystacks = {name: TOKEN_RE.findall(_flatten(value).lower()) for name, value in fields.items()}
        weights = {"summary": 3.0, "transcript": 2.2, "tags": 3.4, "topics": 2.8, "activities": 2.5, "positive": 2.4, "issue": 2.4}
        matched: list[str] = []
        score = 0.0
        for term in terms:
            term_score = sum(weights[name] for name, tokens in haystacks.items() if term in tokens)
            if term_score:
                matched.append(term)
                score += term_score
        phrase = " ".join(terms)
        joined = " ".join(_flatten(value).lower() for value in fields.values())
        if len(terms) > 1 and phrase in joined:
            score += 8
        if score:
            normalized = min(1.0, score / max(8.0, len(terms) * 8.5))
            ranked.append(RankedScene(scene, round(normalized, 3), matched))
    return sorted(ranked, key=lambda item: (item.score, item.scene.confidence), reverse=True)


def segment_transcript(segments: list[dict[str, Any]], max_seconds: float = 18) -> list[dict[str, Any]]:
    if not segments:
        return []
    groups: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    group_start = float(segments[0]["start"])
    for segment in segments:
        end = float(segment["end"])
        if current and end - group_start > max_seconds:
            groups.append(_combine(current))
            current = []
            group_start = float(segment["start"])
        current.append(segment)
    if current:
        groups.append(_combine(current))
    return groups


def _combine(items: list[dict[str, Any]]) -> dict[str, Any]:
    start, end = float(items[0]["start"]), float(items[-1]["end"])
    return {
        "start_seconds": start,
        "end_seconds": end,
        "start_timestamp": format_timestamp(start),
        "end_timestamp": format_timestamp(end),
        "text": " ".join(str(item.get("text", "")).strip() for item in items).strip(),
    }

