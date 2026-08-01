# Devpost submission draft

## Short description

**AARchive turns training footage into searchable lessons.**

Emergency-response trainers, simulation teams, and instructors can own hours of valuable exercise footage yet still struggle to retrieve one useful moment. AARchive uploads authorized MP4 footage directly to Backblaze B2, extracts timestamped evidence with FFmpeg and AI, organizes conservative scene observations, and lets reviewers search across transcript language, activities, equipment, environment, and corrected metadata.

Open any search result at the exact video moment, mark machine observations accurate or in need of correction, then select evidence to generate an after-action brief. A real Genblaze pipeline produces a professional cover image and narrated briefing through supported OpenAI media adapters, persists the outputs and canonical provenance manifests to B2, and exposes useful non-secret verification fields alongside the brief.

The demo includes public-domain emergency-response exercise footage, a seeded search, and a reviewable brief so judges can understand the product immediately. Seeded assets that do not have a live manifest are explicitly labeled unverified; AARchive never fabricates a successful generation or processing state.

This prototype uses only public, synthetic, reenacted, or user-created footage. It is not affiliated with, approved by, or deployed by the Department of Defense or I/ITSEC and makes no government compliance claims.

## Three-minute demo-video outline

### 0:00–0:20 — Problem and promise

- Open the AARchive library.
- Say: “Training teams may own hours of useful footage, but finding one moment often requires knowing the exact file and timestamp. AARchive turns training footage into searchable lessons.”
- Point out the public-demo label and data-use disclaimer.

### 0:20–0:50 — B2-backed organization

- Show video cards, processing states, indexed-scene counts, brief counts, and B2 storage indicators.
- Open the seeded emergency-response exercise.
- Explain the object layout: source, frames, transcript, scenes, corrections, logs, and briefs under one project prefix.

### 0:50–1:25 — Search exact moments

- Search “equipment problem followed by a recovery.”
- Show ranked timestamps, summary, transcript excerpt, tags, confidence, and verification state.
- Select **Open moment** and show the player seeking to `00:32`.

### 1:25–1:50 — Human verification

- Open the scene observation panel.
- Mark one scene **Accurate** and one **Needs correction**.
- Explain that the correction is stored separately, preserves the AI output, and takes precedence in later search.

### 1:50–2:30 — Generate the brief

- Select the triage and transport scenes.
- Open **Generate After-Action Brief**.
- Show situation, what occurred, positive behavior, improvement opportunity, questions, and source timestamps.
- Play a few seconds of narration and show the cover.

### 2:30–2:50 — Genblaze provenance

- Open the provenance panel.
- Name the real `Pipeline`, OpenAI image/TTS adapters, B2 `ObjectStorageSink`, model names, asset SHA-256 values, canonical manifest hash, generation date, and verification status.
- Note that the seeded local preview is honestly unverified; a configured live run populates verified fields.

### 2:50–3:00 — Close

- Return to the linked source timestamps.
- Say: “B2 is the durable knowledge library. Genblaze makes every generated media brief reproducible and verifiable. AARchive helps teams find the moment and carry the lesson forward.”

