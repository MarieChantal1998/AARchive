"""Generate one cached local brief and persist it to B2 through Genblaze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from aarchive.genblaze_service import GenblazeBriefService
from aarchive.keys import brief_key, metadata_key
from aarchive.models import BriefRequest
from aarchive.search import apply_correction
from aarchive.settings import Settings
from aarchive.storage import B2Store, StorageUnavailable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("scene_ids", nargs="+")
    args = parser.parse_args()

    settings = Settings(_env_file=Path(__file__).resolve().parents[2] / ".env")
    if settings.generation_provider != "local" or settings.generation_mode != "generate_once":
        raise SystemExit("Set GENERATION_PROVIDER=local and GENERATION_MODE=generate_once")
    store = B2Store(settings)
    if not store.connected():
        raise SystemExit("Backblaze B2 is not connected")

    request = BriefRequest(project_id=args.project_id, scene_ids=args.scene_ids)
    service = GenblazeBriefService(settings)
    cached_key = brief_key(args.project_id, service.brief_id_for(request), "brief.json")
    try:
        existing = store.get_json(cached_key)
    except StorageUnavailable:
        existing = None
    if existing:
        project = store.get_project(args.project_id)
        if project.brief_count < 1:
            project.brief_count = 1
            store.put_json(metadata_key(args.project_id, "project"), project)
        print(json.dumps({"status": "cached", "brief_id": existing.get("brief_id")}))
        return

    project = store.get_project(args.project_id)
    corrections = {item.scene_id: item for item in store.get_corrections(args.project_id)}
    scene_map = {
        scene.scene_id: apply_correction(scene, corrections.get(scene.scene_id))
        for scene in store.get_scenes(args.project_id)
    }
    selected = [scene_map[scene_id] for scene_id in args.scene_ids]
    brief = service.generate(request, project.title, selected)
    store.put_json(cached_key, brief)
    project.brief_count += 1
    store.put_json(metadata_key(args.project_id, "project"), project)
    print(
        json.dumps(
            {
                "status": "generated",
                "brief_id": brief.brief_id,
                "provider": brief.provider,
                "models": brief.models,
                "cover_url": brief.cover_url,
                "narration_url": brief.narration_url,
                "manifest_uri": brief.manifest_uri,
                "manifest_hash": brief.manifest_hash,
                "verification_status": brief.verification_status,
            }
        )
    )


if __name__ == "__main__":
    main()
