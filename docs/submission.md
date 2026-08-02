# Devpost submission draft

## Short description

**AARchive turns training footage into searchable lessons.**

Emergency-response trainers, simulation teams, and instructors may own hours of valuable exercise footage yet still struggle to retrieve one useful moment. AARchive uploads authorized MP4 footage directly to Backblaze B2, extracts audio and frames with FFmpeg, creates a timestamped local Whisper transcript, and organizes conservative machine observations into searchable scenes.

Search in ordinary language, open a result at its exact timestamp, and correct machine metadata without overwriting the original observation. Select scenes to open a previously generated after-action brief containing a professional lesson card, a 19.50-second neural narration, discussion questions, and linked source timestamps.

The AI media workflow uses **NVIDIA / `nvidia/magpie-tts-multilingual`** through a real Genblaze `Pipeline`. After one short validation, Magpie generated the after-action narration once with the Aria voice. Genblaze’s `ObjectStorageSink` persisted the WAV and genuine canonical provenance manifest to Backblaze B2. The professional Pillow lesson-card cover from the earlier verified Genblaze run is retained, with its original asset and manifest preserved separately. The public demo reads private B2 objects through short-lived presigned URLs and never triggers repeat generation.

The verified workflow uses a real synthetic MP4 and cost $0. NVIDIA Magpie run `57dd1528-8e44-4654-bb9d-688f57c067c1` produced a 19.50-second WAV with SHA-256 `445864cf0f236ff6177e970671f2db49bf2df6ff9b5f9e130d224c4aec41f874`; its manifest verifies with canonical hash `6ba1be1de298ce6039aa2cd28cc944e9e4fd52e707b25a823d5665841b89a2cf`. GMI Cloud and OpenAI remain optional and disabled. Two attempted free NVIDIA FLUX runs failed truthfully and produced failed manifests only; AARchive claims no NVIDIA-generated image.

This prototype uses only public, synthetic, reenacted, or user-created footage. It is not affiliated with, approved by, or deployed by the Department of Defense or I/ITSEC and makes no government compliance claims.

## Three-minute demo-video outline

### 0:00–0:20 — Problem and promise

- Open the [public AARchive library](https://aarchive-lessons.space-girl-in-love.chatgpt.site/).
- Say: “Training teams may own hours of useful footage, but finding one moment often requires knowing the exact file and timestamp. AARchive turns training footage into searchable lessons.”
- Point out the public/synthetic-footage disclaimer.

### 0:20–0:50 — Real B2-backed organization

- Show the real **Synthetic Evacuation and Communications Exercise** card.
- Point out the B2 indicator, ready status, scene count, and generated-brief count.
- Explain that source MP4, audio, frames, transcript, scenes, corrections, processing logs, brief media, and provenance share one B2 project prefix.

### 0:50–1:25 — Search and exact timestamp

- Search **“radio battery recovery”** or **“equipment problem followed by a recovery.”**
- Show corrected `scene-002`, timestamp `00:16–00:34`, transcript excerpt, tags, and relevance.
- Choose **Open moment** and show the player seeking to exactly `16.84` seconds.

### 1:25–1:50 — Human verification

- Show the machine observation and the separate correction record.
- Explain that the human correction says a simulated radio battery issue was followed by backup-radio recovery.
- Re-run the search and show the correction taking precedence.

### 1:50–2:30 — Cached generated brief

- Select scenes 1–3 and choose **Generate After-Action Brief**; the endpoint returns the already generated B2 brief without running inference.
- Show situation, what occurred, positive behaviors, improvement opportunity, questions, and timestamps.
- Show the retained lesson-card cover and play several seconds of the 19.50-second NVIDIA Magpie narration.
- Note the label **Previously generated demonstration asset**.

### 2:30–2:50 — Genuine Genblaze provenance

- Open the provenance panel.
- Show pipeline `aarchive-nvidia-magpie-narration`, provider **NVIDIA**, audio model `nvidia/magpie-tts-multilingual`, run `57dd1528-8e44-4654-bb9d-688f57c067c1`, storage sink, audio SHA-256, verified state, and canonical manifest hash `6ba1be1d…`.
- Explain that Pillow provides the retained lesson-card cover, while the actual generative-AI media evidence is the hosted neural Magpie narration.
- Explain that the private asset URLs are presigned at response time and playback does not regenerate media.

### 2:50–3:00 — Close

- Return to the linked source timestamps.
- Say: “B2 is the durable knowledge library. Genblaze makes the generated media traceable and verifiable. AARchive helps teams find the moment and carry the lesson forward.”
