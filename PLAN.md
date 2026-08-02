# AARchive MVP execution plan

1. **Complete:** establish the TypeScript/FastAPI repository, configuration contract, B2 object layout, and unchanged seeded demo.
2. **Complete:** deploy the public frontend and free Render backend; connect health, CORS, and the real B2 bucket.
3. **Complete:** upload and process a synthetic MP4 into B2 source, audio, frames, transcript, scenes, and logs.
4. **Complete:** verify search ranking, exact `16.84`-second seeking, separate human corrections, and correction precedence.
5. **Complete:** run a real two-step Genblaze Pipeline with the $0 local media fallback; persist one PNG, one 67-second MP3, one verified manifest, and `brief.json` to B2.
6. **Complete:** deploy private-brief presigning; verify public search, `16.84`-second seeking, the B2 cover and 67-second narration, provenance, and cached-only behavior; then pass the full test and secret-scan checklist.

Demo reliability and truthful status take priority over optional scope. GMI Cloud and OpenAI remain disabled; NVIDIA failures are recorded as failed runs and never represented as successful outputs.
