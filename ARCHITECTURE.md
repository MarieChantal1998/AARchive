# AARchive architecture

```mermaid
flowchart LR
    U["Browser"] --> F["Next.js frontend on Sites"]
    U -->|"presigned upload"| B2["Private Backblaze B2 bucket"]
    F -->|"JSON"| API["FastAPI on Render Free"]
    API -->|"durable JSON + presigned media"| B2
    API --> W["Background video processor"]
    W --> FF["FFmpeg"]
    W --> STT["faster-whisper tiny.en"]
    W --> LocalAnalysis["local segmentation and conservative tags"]
    LocalRun["Preserved local cover run"] --> CoverG["Genblaze cover Pipeline"]
    CoverG --> IMG["Pillow lesson-card SyncProvider"]
    HostedRun["One-time hosted neural run"] --> AudioG["Genblaze audio Pipeline"]
    AudioG --> TTS["NVIDIA / nvidia-magpie-tts-multilingual"]
    CoverG -->|"hierarchical ObjectStorageSink"| B2
    AudioG -->|"hierarchical ObjectStorageSink"| B2
```

## Runtime boundaries

- The frontend contains no provider or B2 credentials. It loads application JSON through FastAPI and receives short-lived media URLs.
- FastAPI owns validation, presigning, metadata access, search, corrections, cached-brief lookup, and safe provenance responses.
- B2 is the durable system of record. Local disk is temporary processing or generation workspace only.
- The processor downloads the source into a temporary directory, uses FFmpeg and faster-whisper, uploads all outputs, and removes the directory in `finally` cleanup.
- The retained cover was created by the original two-step local Genblaze Pipeline. The public brief’s current narration was created once by a separate real Genblaze Pipeline using hosted NVIDIA Magpie neural TTS and persisted with the Backblaze-compatible storage sink.
- `brief.json` keeps durable credential-free B2 object URLs. API responses replace those with one-hour presigned URLs for the private bucket.

## Search and verification

Corrected scene metadata overrides original machine fields before deterministic phrase/token/tag scoring. Corrections remain separate in `corrections.json`; the original `scenes.json` is preserved.

## Generated-media provenance

Successful NVIDIA run `57dd1528-8e44-4654-bb9d-688f57c067c1` contains the 19.50-second Magpie WAV and its canonical manifest. The current brief stores the actual provider/model identifiers, audio SHA-256, manifest URI and hash, and verification status. Original local run `b41e0cca-332b-4259-be84-c0518be665dd` and `brief.local-fallback.json` preserve the Pillow cover and local fallback narration history. Two earlier NVIDIA image failures remain as failed manifests and are never presented as successful media.

## B2 object layout

```text
projects/{project_id}/
  source/original.mp4
  audio/extracted.wav
  frames/frame-0001.jpg
  metadata/project.json
  metadata/transcript.json
  metadata/scenes.json
  metadata/corrections.json
  metadata/processing-log.json
  briefs/{brief_id}/brief.json
  briefs/{brief_id}/brief.local-fallback.json
  briefs/{brief_id}/genblaze/runs/{date}/{run_id}/
    assets/{asset_id}.png
    assets/{asset_id}.mp3
    manifest.json
  briefs/{brief_id}/genblaze-nvidia-narration/runs/{date}/{run_id}/
    assets/{asset_id}.wav
    manifest.json
```
