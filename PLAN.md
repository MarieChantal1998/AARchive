# AARchive MVP execution plan

1. Establish the monorepo, configuration contract, B2 object layout, and seeded demo data.
2. Build the FastAPI API for B2-backed projects, upload signing, processing states, scene search, corrections, and briefs.
3. Implement FFmpeg extraction, timestamped transcript segmentation, conservative AI analysis, and retryable processing.
4. Integrate a real Genblaze `Pipeline` with OpenAI image + TTS providers and a Backblaze B2 object-storage sink; retain and expose safe provenance fields.
5. Build the responsive library, upload, search, video-detail, and brief-detail experiences around one preprocessed public/synthetic demo.
6. Add focused frontend/backend tests, complete documentation, validate builds, and deploy the frontend plus a documented backend service target.

Demo reliability takes priority over optional scope. Missing cloud credentials must produce explicit capability states, while the seeded B2-compatible demo remains browsable and searchable.
