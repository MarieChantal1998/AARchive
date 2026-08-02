"""Verify a cached brief, its Genblaze manifest, and B2 media hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from genblaze_core.models.manifest import parse_manifest

from aarchive.keys import brief_key
from aarchive.models import Brief
from aarchive.settings import Settings
from aarchive.storage import B2Store


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id")
    parser.add_argument("brief_id")
    args = parser.parse_args()

    settings = Settings(_env_file=Path(__file__).resolve().parents[2] / ".env")
    store = B2Store(settings)
    brief = Brief.model_validate(
        store.get_json(brief_key(args.project_id, args.brief_id, "brief.json"))
    )
    manifest_key = store._key_from_storage_url(brief.manifest_uri)
    cover_key = store._key_from_storage_url(brief.cover_url)
    narration_key = store._key_from_storage_url(brief.narration_url)
    if not manifest_key or not cover_key or not narration_key:
        raise SystemExit("Brief contains an invalid durable B2 asset URL")

    manifest = parse_manifest(store.get_json(manifest_key))
    verification = manifest.verify()
    cover = store.client.get_object(Bucket=settings.b2_bucket, Key=cover_key)["Body"].read()
    narration = store.client.get_object(Bucket=settings.b2_bucket, Key=narration_key)["Body"].read()
    cover_sha = hashlib.sha256(cover).hexdigest()
    narration_sha = hashlib.sha256(narration).hexdigest()

    ffprobe = shutil.which("ffprobe")
    duration = None
    if ffprobe:
        with tempfile.NamedTemporaryFile(suffix=".mp3") as audio_file:
            audio_file.write(narration)
            audio_file.flush()
            completed = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    audio_file.name,
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            duration = round(float(completed.stdout.strip()), 2)

    evidence = {
        "brief_id": brief.brief_id,
        "run_id": brief.provenance.get("run_id"),
        "provider": brief.provider,
        "models": brief.models,
        "manifest_key": manifest_key,
        "manifest_hash": manifest.canonical_hash,
        "manifest_matches_brief": manifest.canonical_hash == brief.manifest_hash,
        "manifest_verified": bool(verification),
        "cover_key": cover_key,
        "cover_bytes": len(cover),
        "cover_sha256_matches": cover_sha == brief.provenance.get("image_sha256"),
        "narration_key": narration_key,
        "narration_bytes": len(narration),
        "narration_sha256_matches": narration_sha == brief.provenance.get("audio_sha256"),
        "narration_duration_seconds": duration,
    }
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
