"use client";

import Link from "next/link";
import { ArrowRight, CheckSquare2, Filter, Play, Sparkles, Square } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { SearchBox } from "../components/SearchBox";
import { scenes, searchScenes, suggestedQueries } from "../lib/demo-data";
import { ApiBrief, ApiSearchResult, apiFetch } from "../lib/api";

type ResultItem = {
  projectId: string;
  videoTitle: string;
  scene: (typeof scenes)[number];
  matched: string[];
  relevance: number;
  verification: string;
};

export function SearchExperience() {
  const params = useSearchParams();
  const router = useRouter();
  const query = params.get("q") || "effective team coordination";
  const [selected, setSelected] = useState<string[]>([]);
  const [tag, setTag] = useState("All tags");
  const [remoteResults, setRemoteResults] = useState<ResultItem[] | null>(null);
  const [sourceLabel, setSourceLabel] = useState("Searching the connected B2 index…");
  const [generationError, setGenerationError] = useState("");
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    apiFetch<ApiSearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`, undefined, 60000).then((items) => {
      setRemoteResults(items.map((item) => ({
        projectId: item.project_id,
        videoTitle: item.video_title,
        matched: item.matched_terms,
        relevance: item.relevance,
        verification: item.verification_status,
        scene: {
          id: item.scene.scene_id,
          start: item.scene.start_seconds,
          end: item.scene.end_seconds,
          range: `${item.scene.start_timestamp}–${item.scene.end_timestamp}`,
          summary: item.scene.summary,
          excerpt: item.scene.transcript_excerpt,
          tags: item.scene.search_tags,
          confidence: Math.round(item.scene.confidence * 100),
          issue: item.scene.observed_issue || undefined,
          positive: item.scene.observed_positive_behavior || undefined,
          activities: item.scene.activities,
          roles: item.scene.people_or_roles,
          equipment: item.scene.equipment,
          environment: item.scene.location_or_environment,
        },
      })));
      setSourceLabel("Ranked by the FastAPI index loaded from B2 metadata");
    }).catch(() => {
      const seeded = searchScenes(query).map(({scene, matched, score}) => ({
        projectId: "demo-coordinated-response", videoTitle: "Integrated Emergency Response Exercise",
        scene, matched, relevance: Math.min(1, score / 4), verification: "unreviewed",
      }));
      setRemoteResults(seeded);
      setSourceLabel("Seeded demonstration · backend unavailable");
    });
  }, [query]);

  const results = useMemo(() => {
    const available = remoteResults || [];
    return tag === "All tags" ? available : available.filter((item) => item.scene.tags.includes(tag));
  }, [remoteResults, tag]);
  const allTags = ["All tags", "coordination", "triage", "handoff", "transport"];
  function toggle(key: string) {
    setSelected((current) => current.includes(key) ? current.filter((item) => item !== key) : [...current, key]);
  }
  async function generateBrief() {
    const chosen = results.filter((item) => selected.includes(`${item.projectId}:${item.scene.id}`));
    const projectId = chosen[0]?.projectId;
    if (!projectId || chosen.some((item) => item.projectId !== projectId)) {
      setGenerationError("Select scenes from one video at a time."); return;
    }
    if (projectId === "demo-coordinated-response") {
      router.push("/briefs/11111111-1111-4111-8111-111111111111?project=demo-coordinated-response"); return;
    }
    setGenerating(true); setGenerationError("");
    try {
      const brief = await apiFetch<ApiBrief>("/api/briefs", {
        method: "POST",
        body: JSON.stringify({project_id: projectId, scene_ids: chosen.map((item) => item.scene.id)}),
      }, 240000);
      router.push(`/briefs/${brief.brief_id}?project=${projectId}`);
    } catch (reason) {
      setGenerationError(reason instanceof Error ? reason.message : "The cached brief is not available.");
    } finally { setGenerating(false); }
  }
  return (
    <div className="page search-page">
      <header className="page-header"><p className="eyebrow">Search footage</p><h1>Exact moments, <span>not filenames.</span></h1><p className="header-copy">Results combine transcript language, structured observations, tags, and any human corrections.</p></header>
      <SearchBox initial={query} compact />
      <div className="filter-bar">
        <div><Filter size={15} /><span>Filters</span></div>
        <select aria-label="Exercise type"><option>All exercise types</option><option>Emergency response / triage</option></select>
        <select aria-label="Exercise date"><option>Any date</option><option>2026</option></select>
        <select value={tag} onChange={(event) => setTag(event.target.value)} aria-label="Tag">{allTags.map((item) => <option key={item}>{item}</option>)}</select>
      </div>
      <div className="results-heading"><div><p className="eyebrow">Ranked results</p><h2>{results.length} moments for “{query}”</h2><span className="muted">{sourceLabel}</span></div><span className="ai-observation"><Sparkles size={14} /> Machine observations · verify before use</span></div>
      <div className="results-list">
        {results.map(({ scene, matched, projectId, videoTitle, relevance, verification }, index) => {
          const selectionKey = `${projectId}:${scene.id}`;
          const checked = selected.includes(selectionKey);
          return (
            <article className="result-card" key={selectionKey}>
              <button className="select-scene" onClick={() => toggle(selectionKey)} aria-label={`${checked ? "Deselect" : "Select"} ${scene.range}`}>{checked ? <CheckSquare2 /> : <Square />}</button>
              <div className="rank">{String(index + 1).padStart(2, "0")}</div>
              <div className="result-content">
                <div className="result-kicker"><span>{videoTitle}</span><strong>{scene.range}</strong></div>
                <h3>{scene.summary}</h3>
                <blockquote>“{scene.excerpt}”</blockquote>
                <div className="tag-row">{scene.tags.map((item) => <span className={matched.includes(item) ? "matched" : ""} key={item}>{item}</span>)}</div>
              </div>
              <div className="result-actions"><span className="relevance"><i style={{ width: `${Math.round(relevance * 100)}%` }} />{Math.round(relevance * 100)}% relevance · {verification}</span><Link className="button secondary" href={`/videos/${projectId}?t=${scene.start}&scene=${scene.id}`}><Play size={15} fill="currentColor" /> Open moment</Link></div>
            </article>
          );
        })}
      </div>
      {selected.length > 0 && <div className="selection-bar"><div><strong>{selected.length} scene{selected.length > 1 ? "s" : ""} selected</strong><span>{generationError || "Source timestamps will be carried into the brief."}</span></div><button className="button primary" onClick={generateBrief} disabled={generating}>{generating ? "Checking cached brief…" : "Generate After-Action Brief"} <ArrowRight size={16} /></button></div>}
      <div className="query-suggestions"><span>Other searches</span>{suggestedQueries.map((item) => <Link key={item} href={`/search?q=${encodeURIComponent(item)}`}>{item}</Link>)}</div>
    </div>
  );
}
