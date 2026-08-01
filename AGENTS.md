# AARchive contributor guide

## Product guardrails

- Use only public, synthetic, reenacted, or user-created footage.
- Never imply Department of Defense, I/ITSEC, or government approval, affiliation, compliance, or deployment.
- Treat all AI scene descriptions as machine-generated observations requiring human review.
- Do not add facial or identity recognition, threat identification, targeting, personnel rankings, readiness scores, classified-data support, or live battlefield analysis.

## Engineering priorities

1. Preserve the end-to-end demo: library → search → timestamp seek → scene selection → brief → provenance.
2. Backblaze B2 is the durable source of truth for media and JSON metadata; do not add a database without a demonstrated need.
3. Genblaze generation must use its real `Pipeline`, a supported provider, `ObjectStorageSink`, and persisted manifest.
4. Never fabricate a successful upload, processing run, generation, or verification state.
5. Keep secrets server-side and return only allowlisted provenance/configuration fields.

## Repository conventions

- Frontend: Next-compatible TypeScript app at the repository root.
- Backend: Python 3.11+ FastAPI app under `backend/`.
- Use UUIDs for internal identifiers and sanitized filenames only for display metadata.
- Keep B2 keys under `projects/{project_id}/...`.
- Run `npm test` and `npm run test:all` before handoff.
