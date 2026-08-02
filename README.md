# AARchive

**Turn training footage into searchable lessons.**

AARchive turns public, synthetic, reenacted, or user-created training footage into searchable timestamped observations and reusable after-action training briefs.

- Public app: [aarchive-lessons.space-girl-in-love.chatgpt.site](https://aarchive-lessons.space-girl-in-love.chatgpt.site/)
- FastAPI backend: [aarchive-api.onrender.com](https://aarchive-api.onrender.com/health)
- Public repository: [github.com/MarieChantal1998/AARchive](https://github.com/MarieChantal1998/AARchive)

This is a two-day hackathon prototype. It is not approved by, affiliated with, or deployed by the Department of Defense or I/ITSEC. It is not designed for classified or sensitive operational data.

## Product overview

Training teams can accumulate hours of useful exercise footage while remaining unable to retrieve a specific moment without already knowing its filename and timestamp. AARchive makes footage addressable: upload an MP4, extract timestamped evidence, search in ordinary language, verify scene observations, and assemble selected moments into a narrated brief linked to source timestamps.

The public app includes both an unchanged seeded demonstration and a real processed synthetic exercise stored in Backblaze B2. The real project can be searched, opened at `16.84` seconds, corrected, and linked to a previously generated B2-hosted brief.

## Verified deployment status

| Capability | Verified state | Evidence |
|---|---|---|
| Frontend | Publicly deployed | OpenAI Sites URL above |
| Backend | Publicly deployed on Render Free | `/health` reports B2 connected |
| GitHub | Public and pushed | `master`, latest repository URL above |
| Video workflow | End-to-end verified | Synthetic MP4, audio, frames, transcript, scenes, logs in B2 |
| Search and seeking | End-to-end verified | Corrected `scene-002`, `16.84–34.64`, seeks to `16.84` |
| Human correction | End-to-end verified | Separate B2 correction overrides the machine observation |
| Genblaze media | End-to-end verified | Run `b41e0cca-332b-4259-be84-c0518be665dd` |
| Generated cover | Connected to real B2 | 59,055-byte PNG; SHA-256 verified |
| Generated narration | Connected to real B2 | 67-second MP3; SHA-256 verified |
| Provenance | Connected to real B2 | Canonical hash `18d39e64d0207aba9956f5b1c21e86c2f940b720dc2bbd03e59c0b8ac344e3b0` |
| Public regeneration | Disabled | Backend remains `cached_only` |

No paid service, card, automatic billing, or automatic reload was activated.

## Architecture

```mermaid
flowchart LR
    Browser --> Frontend["Next.js / TypeScript frontend"]
    Browser -->|"presigned MP4 PUT"| B2["Backblaze B2"]
    Frontend -->|"JSON API"| API["FastAPI on Render Free"]
    API -->|"private presigned reads / durable JSON"| B2
    API --> Processor["FFmpeg + faster-whisper + local scene analysis"]
    Processor --> B2
    LocalRun["One-time local media run"] --> Pipeline["Real Genblaze Pipeline"]
    Pipeline --> Card["Pillow lesson-card provider"]
    Pipeline --> TTS["macOS Say + FFmpeg narration provider"]
    Pipeline -->|"ObjectStorageSink + canonical manifest"| B2
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for boundaries and object layout.

## User workflow

1. Open the library or upload an authorized MP4 directly to B2 with a presigned URL.
2. Process the footage with FFmpeg, local Whisper transcription, timestamp segmentation, and conservative machine observations.
3. Search transcript text, summaries, tags, and human-corrected fields.
4. Choose **Open moment** to seek the source video to the result’s `start_seconds`.
5. Mark an observation accurate or needing correction; corrections remain separate and take precedence.
6. Select scenes and open the cached after-action brief.
7. Review the cover, 67-second narration, timestamps, provider/model fields, hashes, and provenance.

## Backblaze B2 usage

B2 is the durable system of record, not a backup. The public library reads real project JSON from B2. Source video, extracted audio, frames, transcript, scenes, corrections, processing logs, brief JSON, generated media, and Genblaze manifests all live under the project prefix. Source uploads use presigned direct PUTs; private video and brief assets are returned through short-lived presigned GET URLs.

Verified bucket: `aarchive-nyirachantal1998-media`. The workflow remains well within Backblaze’s included 10 GB allowance.

## Genblaze usage

The successful demonstration uses a real `genblaze-core` `Pipeline` with two custom `SyncProvider` implementations:

- `LocalLessonCardProvider`, model `pillow-lesson-card-v1`, renders a prompt-derived professional training lesson card with open-source Pillow;
- `LocalNarrationProvider`, model `macos-say-tts-v1`, creates offline narration with macOS Say and encodes it to MP3 with FFmpeg;
- `S3StorageBackend.for_backblaze(...)` and `ObjectStorageSink` persist assets and the provenance manifest to B2;
- `KeyStrategy.HIERARCHICAL` preserves Genblaze’s run layout;
- `max_retries=0` prevents duplicate expensive work;
- asset SHA-256 values, the canonical manifest hash, manifest URI, run ID, and verification result are recorded in `brief.json`.

This fallback is intentionally described as local automated media generation, not as diffusion-model image generation. It costs $0, uses no hosted inference API, and preserves meaningful Genblaze execution and provenance.

The current `genblaze-nvidia==0.3.3` adapter was also integrated and exercised with the free NVIDIA trial. Magpie’s current hosted Riva preflight succeeded, but two FLUX attempts failed truthfully with a read timeout and a provider-side `504`; Genblaze stored failed-run manifests and no NVIDIA media was claimed. GMI Cloud and OpenAI integrations remain optional but disabled because no funded API service is available.

Official implementation references: [Genblaze repository](https://github.com/backblaze-labs/genblaze), [Backblaze Genblaze Developer Guide](https://www.backblaze.com/docs/cloud-storage-genblaze-developer-guide), [Genblaze on PyPI](https://pypi.org/project/genblaze/), and [NVIDIA Magpie TTS API](https://build.nvidia.com/nvidia/magpie-tts-multilingual/api).

## Providers and models actually used

| Purpose | Actual provider / model | Cost |
|---|---|---|
| Transcription | local `faster-whisper`, `tiny.en` | $0 |
| Scene structuring | deterministic local transcript segmentation and conservative tag analysis | $0 |
| Brief text | deterministic selected-scene assembly with human-correction precedence | $0 |
| Brief cover | Pillow `pillow-lesson-card-v1` through Genblaze | $0 |
| Narration | macOS Say `macos-say-tts-v1`, Samantha at 155 wpm, encoded by FFmpeg | $0 |
| Durable storage | Backblaze B2 S3-compatible API and Genblaze S3 sink | Free allowance |

Optional disabled providers: GMI Cloud image/audio, NVIDIA NIM image/Magpie TTS, and OpenAI image/TTS. OpenAI is never selected unless `OPENAI_API_KEY` is present and funded billing is explicitly available.

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
  briefs/{brief_id}/
    brief.json
    genblaze/runs/{date}/{run_id}/
      assets/{asset_id}.png
      assets/{asset_id}.mp3
      manifest.json
```

## How B2 and Genblaze Are Essential

B2 makes AARchive’s searchable library durable: removing it removes the real videos, timestamp metadata, corrections, generated media, and provenance. Genblaze turns the cover and narration into one traceable media workflow: removing it removes the run manifest, canonical hash, asset hashes, verification result, and hierarchical B2 persistence.

The successful cached brief is not a static file copied into the frontend. It is loaded from B2 through FastAPI, and its media URLs are presigned at response time because the bucket is private.

## Local setup

Requirements: Node 22.13+, Python 3.11+, and FFmpeg. The zero-cost local narration provider additionally requires macOS Say.

```bash
cp .env.example .env
npm install
python3 -m venv /tmp/aarchive-venv
source /tmp/aarchive-venv/bin/activate
pip install -e 'backend[dev]'
```

Run the services in separate terminals:

```bash
npm run dev
```

```bash
source /tmp/aarchive-venv/bin/activate
uvicorn aarchive.main:app --app-dir backend --reload --port 8000
```

Open `http://localhost:3000`; API documentation is at `http://localhost:8000/docs`.

## Environment variables

Server-only B2 settings:

- `B2_ENDPOINT_URL`, `B2_REGION`, `B2_BUCKET`, `B2_KEY_ID`, `B2_APP_KEY`
- `B2_PUBLIC_URL_BASE` only for an intentionally public bucket; omit it for presigned reads

Provider and processing settings:

- `TRANSCRIPTION_PROVIDER=local_whisper`, `LOCAL_WHISPER_MODEL=tiny.en`, `ANALYSIS_PROVIDER=local`
- `GENERATION_MODE=cached_only` in public deployments
- `LOCAL_IMAGE_MODEL`, `LOCAL_AUDIO_MODEL`, `LOCAL_TTS_VOICE`, `LOCAL_TTS_RATE`
- optional `GMI_API_KEY`, `NVIDIA_API_KEY`, or `OPENAI_API_KEY`; never expose these to the frontend

Deployment settings:

- `NEXT_PUBLIC_API_URL` is the only frontend-visible API setting
- `FRONTEND_ORIGINS`, `MAX_UPLOAD_MB`, `PROCESSING_TIMEOUT_SECONDS`, `GENERATION_TIMEOUT_SECONDS`

Never commit `.env` or place credentials in `NEXT_PUBLIC_*` values.

## Deployment

### Frontend

The frontend is deployed with OpenAI Sites from the project containing `.openai/hosting.json`. Its configured backend is `https://aarchive-api.onrender.com`.

```bash
npm run build
```

### Backend

`render.yaml` and `backend/Dockerfile` define the FastAPI service. The verified deployment uses Render’s free web-service plan, so an idle cold start may add roughly 50 seconds. No paid Render plan is required.

```bash
docker build -f backend/Dockerfile -t aarchive-api .
docker run --env-file .env -p 8000:8000 aarchive-api
```

Set secrets only in the host dashboard, add the Sites origin to `FRONTEND_ORIGINS`, and verify `/health` before connecting the frontend.

## Demo credentials

None. The public app and cached B2 brief require no judge-supplied API key. Public regeneration is disabled, so viewing or replaying the generated media does not trigger inference.

## Testing

Run frontend lint/build/tests and all backend tests:

```bash
npm run test:all
```

If the virtual environment is not activated:

```bash
AARCHIVE_PYTHON=/path/to/venv/bin/python npm run test:all
```

Verify a cached brief directly against B2 without printing credentials:

```bash
cd backend
python -m scripts.verify_cached_brief PROJECT_ID BRIEF_ID
```

Tests cover B2 keys, metadata validation, segmentation, ranking, timestamps, correction precedence, Genblaze abstractions, current NVIDIA TTS transport, local media generation, private-asset presigning, failure states, and credential leakage.

## Security limitations

- MP4 type/size validation, UUID identifiers, fixed object-key builders, direct B2 uploads, and temporary-directory cleanup are implemented.
- Provider and B2 credentials remain server-side. Private B2 assets use one-hour presigned response URLs.
- CORS is explicit; generation has timeouts and zero automatic retries.
- This prototype has no user authentication, malware scanning, tenant isolation, durable task queue, or complex role-based access control.
- It is not FedRAMP, CMMC, military, classified-data, or government-security compliant and makes no such claim.

## Public/synthetic-data disclaimer

Use only footage that is public, synthetic, reenacted, or user-created and authorized for upload. The seeded public-domain footage and real synthetic exercise do not imply government endorsement, affiliation, deployment, or approval. Machine observations may be incomplete or wrong and require qualified human review.

## Known limitations

- Search uses deterministic weighted terms and tags rather than embeddings.
- Processing runs as an in-process FastAPI background task instead of a durable queue.
- The successful $0 cover is a professionally composed lesson card, not a diffusion-model image.
- Offline narration generation currently requires macOS; the generated 67-second MP3 is cached in B2 for the public demo.
- The NVIDIA hosted FLUX trial returned a provider-side `504`, so no NVIDIA-generated image is claimed.
- Render Free can cold-start after inactivity.

## Future roadmap

- GMI Cloud media generation if hackathon credits become available
- Durable task queue and resumable multipart uploads
- Embeddings-based hybrid retrieval
- Scene-boundary vision analysis and reviewer edit history
- Authentication, tenant isolation, and malware scanning
- Brief export to PDF/Slides and signed provenance verification

## Submission materials

See [docs/submission.md](docs/submission.md) for the Devpost-ready description and three-minute demo outline.
