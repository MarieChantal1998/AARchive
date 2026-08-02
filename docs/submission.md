# Devpost submission package

## Project name

**AARchive: The After-Action Review Archive**

## Tagline

**Turn training footage into searchable lessons.**

## Project description

AARchive turns public, synthetic, reenacted, or user-created training footage into searchable, timestamped observations and reusable after-action training briefs. A user can upload an authorized MP4 directly to Backblaze B2, process it with FFmpeg and local Whisper, search the transcript and scene metadata in ordinary language, open an exact video moment, preserve a human correction separately from the original machine observation, and review a narrated brief linked to its source timestamps.

The public demonstration includes one real processed synthetic exercise and one previously generated brief. Judges do not need credentials, and viewing or replaying the cached brief cannot trigger a provider call.

## Real-world problem

Training teams may own hours of valuable exercise footage yet still be unable to retrieve one useful moment unless someone already knows the recording and timestamp. That makes footage expensive to review and difficult to reuse. AARchive makes each scene addressable and turns selected moments into a reviewable lesson while keeping machine observations visibly subject to human verification.

## Working links

- Public app: https://aarchive-lessons.space-girl-in-love.chatgpt.site/
- Public repository: https://github.com/MarieChantal1998/AARchive
- Backend health: https://aarchive-api.onrender.com/health

## Backblaze B2 usage

Backblaze B2 is AARchive’s durable system of record, not a backup. The private bucket stores the original synthetic MP4, FFmpeg audio and frames, timestamped transcript, scene metadata, human corrections, processing log, brief JSON, media assets, and Genblaze provenance manifests under one project prefix. Uploads use presigned direct PUT URLs; the public app receives short-lived presigned GET URLs for video, cover, narration, and manifest access. The library and verified brief are loaded from B2 through FastAPI.

## Genblaze usage

The genuine generative-media step is hosted neural narration from **NVIDIA / `nvidia/magpie-tts-multilingual`**, voice `Magpie-Multilingual.EN-US.Aria`. It ran through the real Genblaze `Pipeline("aarchive-nvidia-magpie-narration")`. Genblaze’s Backblaze-compatible `ObjectStorageSink` stored the WAV and canonical manifest in B2 using the hierarchical run layout.

Verified run `57dd1528-8e44-4654-bb9d-688f57c067c1` produced a 19.50-second WAV with SHA-256 `445864cf0f236ff6177e970671f2db49bf2df6ff9b5f9e130d224c4aec41f874`. Its canonical manifest hash is `6ba1be1de298ce6039aa2cd28cc944e9e4fd52e707b25a823d5665841b89a2cf`.

The cover is a professional lesson card rendered by Pillow model `pillow-lesson-card-v1` through an earlier Genblaze run. It is not described as an AI-generated image. GMI Cloud and OpenAI integrations remain optional code paths and were not used successfully. Two free NVIDIA FLUX attempts failed and produced failed manifests only; AARchive claims no NVIDIA-generated image.

## Providers and models actually used

| Purpose | Provider and model | Execution |
|---|---|---|
| Neural narration | NVIDIA `nvidia/magpie-tts-multilingual`, Aria voice | Hosted once through Genblaze; $0 trial access |
| Brief cover | Pillow `pillow-lesson-card-v1` | Local deterministic renderer through Genblaze; not generative AI |
| Transcription | `faster-whisper` `tiny.en` | Local |
| Scene structuring and search | Deterministic transcript segmentation, tags, and weighted keyword ranking | Local |
| Brief text | Deterministic selected-scene assembly with correction precedence | Local |
| Durable media and metadata | Backblaze B2 S3-compatible API | Included free allowance |

Public media generation is `cached_only`. OpenAI and GMI Cloud were not used in the verified run, live public regeneration is disabled, and the successful cover is not claimed as AI image generation.

## Production-readiness approach

AARchive uses private B2 objects, presigned direct uploads and downloads, MP4 type and size validation, sanitized UUID-based keys, explicit processing states, separate correction records, canonical manifest hashing, asset SHA-256 values, server-only credentials, CORS restrictions, request timeouts, conservative zero-retry generation, and temporary-file cleanup. The public app, Render FastAPI service, private B2 data, search, timestamp seeking, correction precedence, cached NVIDIA narration, and provenance display were verified together after a Render Free cold start.

The public demo is deliberately cached-only: one verified narration was generated once, persisted through Genblaze to B2, and is replayed through a signed URL. This avoids repeated inference cost while retaining a functional provider integration and reproducible provenance trail.

## Limitations and responsible-use boundary

- The 19.50-second verified narration is shorter than the original 45–90 second target because the NVIDIA trial interface limited a call to 350 characters.
- The cover is a Pillow-rendered lesson card, not a diffusion-generated image.
- Search uses deterministic weighted terms and tags rather than embeddings.
- Processing uses an in-process FastAPI background task rather than a durable queue.
- Render Free may cold-start after inactivity.
- The prototype has no user authentication, tenant isolation, malware scanning, or government-system integration.
- Only public, synthetic, reenacted, or user-created authorized footage is permitted. The prototype is not affiliated with, approved by, or deployed by the Department of Defense or I/ITSEC and makes no classified-data, FedRAMP, CMMC, or government compliance claim.

## Three-minute demo script

### 0:00–0:20 — Problem and promise

- Open https://aarchive-lessons.space-girl-in-love.chatgpt.site/.
- Say: “Training teams may own hours of useful footage, but finding one moment often requires knowing the exact file and timestamp. AARchive turns training footage into searchable lessons.”
- Point out the public/synthetic-footage disclaimer.

### 0:20–0:50 — Real B2-backed library

- Show **Synthetic Evacuation and Communications Exercise**.
- Point out **Stored in Backblaze B2**, Ready, three indexed scenes, and one brief.
- Say: “The MP4, extracted media, transcript, scenes, correction, processing log, brief media, and provenance all live under one private B2 project prefix.”

### 0:50–1:25 — Search and exact timestamp

- Choose the seeded query **Equipment problem followed by a recovery**.
- Show corrected `scene-002`, range `00:16–00:34`, transcript excerpt, tags, and relevance.
- Choose **Open moment** and show the signed B2 video seeking to exactly `16.84` seconds.

### 1:25–1:50 — Human verification

- Show the original machine observation and the separate `needs_correction` record.
- Read the human correction: “A simulated radio battery issue was followed by a backup-radio recovery.”
- Explain that future searches rank the correction without overwriting the original machine output.

### 1:50–2:30 — Previously generated brief

- Open the verified after-action brief.
- Show the situation, events, positive behaviors, improvement opportunity, discussion questions, and linked timestamps.
- Say: “This lesson-card cover was rendered with Pillow through Genblaze; it is not an AI-generated image.”
- Play several seconds of the 19.50-second NVIDIA Magpie neural narration.
- Point out **Previously generated demonstration** and explain that playback reads B2 and triggers no inference.

### 2:30–2:50 — Genuine Genblaze provenance

- Open **View provenance**.
- Show pipeline `aarchive-nvidia-magpie-narration`, provider NVIDIA, model `nvidia/magpie-tts-multilingual`, run `57dd1528-8e44-4654-bb9d-688f57c067c1`, B2 storage sink, audio SHA-256, verified state, and manifest hash `6ba1be1d…`.
- Say: “Genblaze orchestrated the hosted neural TTS run and persisted the media plus canonical provenance to B2.”

### 2:50–3:00 — Close

- Return to the linked timestamps.
- Say: “B2 is the durable knowledge library. Genblaze makes generated media traceable and verifiable. Find the moment. Improve the next exercise.”

## Paste-ready Devpost checklist

- [ ] **Project name:** AARchive: The After-Action Review Archive
- [ ] **Tagline:** Turn training footage into searchable lessons.
- [ ] **Working app URL:** https://aarchive-lessons.space-girl-in-love.chatgpt.site/
- [ ] **GitHub repository:** https://github.com/MarieChantal1998/AARchive
- [ ] **Providers and models:** NVIDIA `nvidia/magpie-tts-multilingual` (Aria voice) through Genblaze; Pillow `pillow-lesson-card-v1` through Genblaze for the non-AI cover; local `faster-whisper` `tiny.en`; Backblaze B2 S3-compatible storage.
- [ ] **B2 and Genblaze usage:** B2 durably stores the source video, processing outputs, searchable metadata, corrections, brief, generated narration, cover, and provenance. A real Genblaze Pipeline used NVIDIA Magpie neural TTS once and persisted its WAV plus canonical manifest through `ObjectStorageSink`; the public demo is cached-only.
- [ ] **Project description:** Paste the **Project description**, **Real-world problem**, **Backblaze B2 usage**, **Genblaze usage**, **Production-readiness approach**, and **Limitations** sections above.
- [ ] **Demo video URL:** Record the script above, upload an accessible approximately three-minute video, and paste its URL into Devpost.
- [ ] **Responsible-use disclosure:** Only public, synthetic, reenacted, or user-created authorized footage; no government affiliation, deployment, approval, or compliance claim.
- [ ] **Final review:** Confirm the app and repository links open without authentication, the video is judge-accessible, and no secret is present in the submission text.
