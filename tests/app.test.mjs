import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("ships the product workflow and removes starter preview", async () => {
  const [library, search, upload, video, brief, layout] = await Promise.all([
    readFile(new URL("app/page.tsx", root), "utf8"),
    readFile(new URL("app/search/SearchExperience.tsx", root), "utf8"),
    readFile(new URL("app/upload/UploadForm.tsx", root), "utf8"),
    readFile(new URL("app/videos/[id]/VideoDetail.tsx", root), "utf8"),
    readFile(new URL("app/briefs/[id]/page.tsx", root), "utf8"),
    readFile(new URL("app/layout.tsx", root), "utf8"),
  ]);
  assert.match(library, /Turn|Find the moment/);
  assert.match(search, /Open moment/);
  assert.match(upload, /Backblaze B2/);
  assert.match(video, /human verification required/i);
  assert.match(brief, /Provenance/);
  assert.match(layout, /AARchive/);
  assert.doesNotMatch([library, search, upload, video, brief, layout].join("\n"), /codex-preview|SkeletonPreview/);
});

test("frontend sources contain no credential-shaped environment access", async () => {
  const sources = await Promise.all([
    "app/page.tsx",
    "app/layout.tsx",
    "app/lib/api.ts",
    "app/lib/demo-data.ts",
    "app/upload/UploadForm.tsx",
    "app/search/SearchExperience.tsx",
  ].map((path) => readFile(new URL(path, root), "utf8")));
  const combined = sources.join("\n");
  assert.doesNotMatch(combined, /B2_APP_KEY|B2_KEY_ID|OPENAI_API_KEY|sk-[A-Za-z0-9]/);
  assert.doesNotMatch(combined, /process\.env\.(?!NEXT_PUBLIC_)/);
});

test("public frontend cannot route judges to a developer loopback API", async () => {
  const api = await readFile(new URL("app/lib/api.ts", root), "utf8");
  assert.match(api, /https:\/\/aarchive-api\.onrender\.com/);
  assert.match(api, /configuredForLoopback/);
  assert.match(api, /runningOnLoopback/);
});

test("brief audio refreshes when seeded state is replaced by a B2 brief", async () => {
  const brief = await readFile(new URL("app/briefs/[id]/page.tsx", root), "utf8");
  assert.match(brief, /<audio key=\{brief\.narration_url\}/);
  assert.match(brief, /src=\{brief\.narration_url\}/);
  assert.doesNotMatch(brief, /<source src=\{brief\.narration_url\}/);
});
