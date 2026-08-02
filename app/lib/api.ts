const PUBLIC_API_URL = "https://aarchive-api.onrender.com";
const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const configuredForLoopback = configuredApiUrl
  ? /^https?:\/\/(localhost|127\.0\.0\.1)(?::|\/|$)/i.test(configuredApiUrl)
  : false;
const runningOnLoopback = typeof window !== "undefined"
  && ["localhost", "127.0.0.1"].includes(window.location.hostname);

// Never send a visitor on the deployed site to their own localhost when a
// developer's local .env was present during a frontend build.
export const API_URL = (
  configuredApiUrl && (!configuredForLoopback || runningOnLoopback)
    ? configuredApiUrl
    : PUBLIC_API_URL
).replace(/\/$/, "");

export type ApiProject = {
  project_id: string;
  title: string;
  exercise_type: string;
  exercise_date: string;
  description?: string | null;
  duration_seconds: number;
  status: string;
  status_message: string;
  thumbnail_url?: string | null;
  video_url?: string | null;
  indexed_scene_count: number;
  brief_count: number;
  storage: "b2" | "public_demo";
  seeded_demo: boolean;
  source_attribution?: string | null;
};

export type ApiScene = {
  scene_id: string;
  start_seconds: number;
  end_seconds: number;
  start_timestamp: string;
  end_timestamp: string;
  summary: string;
  transcript_excerpt: string;
  people_or_roles: string[];
  activities: string[];
  equipment: string[];
  location_or_environment: string[];
  training_topics: string[];
  observed_issue?: string | null;
  observed_positive_behavior?: string | null;
  search_tags: string[];
  confidence: number;
  observation_notice: string;
};

export type ApiSearchResult = {
  project_id: string;
  video_title: string;
  exercise_type: string;
  exercise_date: string;
  scene: ApiScene;
  relevance: number;
  matched_terms: string[];
  verification_status: string;
};

export type ApiBrief = {
  brief_id: string;
  project_id: string;
  title: string;
  situation_summary: string;
  what_occurred: string[];
  positive_behaviors: string[];
  improvement_opportunity: string;
  discussion_questions: string[];
  source_timestamps: Array<{scene_id: string; label: string; start_seconds: number; timestamp: string}>;
  review_notice: string;
  cover_url?: string | null;
  narration_url?: string | null;
  provider: string;
  models: string[];
  generated_at: string;
  manifest_hash?: string | null;
  manifest_uri?: string | null;
  verification_status: string;
  provenance: Record<string, unknown>;
  seeded_demo: boolean;
};

export async function apiFetch<T>(path: string, init?: RequestInit, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {"Content-Type": "application/json", ...(init?.headers || {})},
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${response.status})`);
    }
    return await response.json() as T;
  } finally {
    clearTimeout(timeout);
  }
}

export function formatDuration(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(total / 60);
  const remainder = total % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}
