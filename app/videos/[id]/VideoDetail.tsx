"use client";

import Link from "next/link";
import { Check, ChevronDown, CircleAlert, Database, Edit3, FileText, Play, Search, Sparkles } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { DEMO_THUMBNAIL, DEMO_VIDEO_URL, Scene, scenes as demoScenes } from "../../lib/demo-data";
import { ApiBrief, ApiProject, ApiScene, apiFetch } from "../../lib/api";

type Correction = {scene_id: string; verdict: "accurate" | "needs_correction"; fields: Record<string, unknown>};

function toScene(item: ApiScene): Scene {
  return {
    id: item.scene_id,
    start: item.start_seconds,
    end: item.end_seconds,
    range: `${item.start_timestamp}–${item.end_timestamp}`,
    summary: item.summary,
    excerpt: item.transcript_excerpt,
    tags: item.search_tags,
    confidence: Math.round(item.confidence * 100),
    issue: item.observed_issue || undefined,
    positive: item.observed_positive_behavior || undefined,
    activities: item.activities,
    roles: item.people_or_roles,
    equipment: item.equipment,
    environment: item.location_or_environment,
  };
}

export function VideoDetail({projectId}: {projectId: string}) {
  const params = useSearchParams();
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const seeded = projectId === "demo-coordinated-response";
  const [project, setProject] = useState<ApiProject | null>(seeded ? {
    project_id: projectId, title: "Integrated Emergency Response Exercise",
    exercise_type: "Emergency response / triage", exercise_date: "2026-04-29",
    description: "Seeded public-footage demonstration.", duration_seconds: 57,
    status: "ready", status_message: "Seeded demonstration", thumbnail_url: DEMO_THUMBNAIL,
    video_url: DEMO_VIDEO_URL, indexed_scene_count: 5, brief_count: 1,
    storage: "public_demo", seeded_demo: true,
    source_attribution: "Public-domain exercise footage via Wikimedia Commons / DVIDS.",
  } : null);
  const [sceneList, setSceneList] = useState<Scene[]>(seeded ? demoScenes : []);
  const [active, setActive] = useState(params.get("scene") || (seeded ? demoScenes[0].id : ""));
  const [selected, setSelected] = useState<string[]>([]);
  const [verified, setVerified] = useState<Record<string, string>>({});
  const [draftSummary, setDraftSummary] = useState("");
  const [editing, setEditing] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    apiFetch<{project: ApiProject; scenes: ApiScene[]; corrections: Correction[]}>(`/api/projects/${projectId}`, undefined, 60000).then((detail) => {
      setProject(detail.project);
      const mapped = detail.scenes.map(toScene);
      setSceneList(mapped);
      setActive((current) => current || mapped[0]?.id || "");
      setVerified(Object.fromEntries(detail.corrections.map((item) => [item.scene_id, item.verdict])));
      setMessage("");
    }).catch((reason) => {
      if (!seeded) setMessage(reason instanceof Error ? reason.message : "The B2 project could not be loaded.");
    });
  }, [projectId, seeded]);

  const scene = sceneList.find((item) => item.id === active) || sceneList[0];
  const seekFromUrl = () => {
    const start = Number(params.get("t") || 0);
    if (videoRef.current && Number.isFinite(start)) videoRef.current.currentTime = start;
  };
  useEffect(seekFromUrl, [params]);

  if (!project || !scene) return <div className="page"><p>{message || "Loading B2 project metadata…"}</p></div>;

  function openScene(id: string, start: number) {
    setActive(id);
    const selectedScene = sceneList.find((item) => item.id === id);
    setDraftSummary(selectedScene?.summary || "");
    setEditing(false);
    if (videoRef.current) {
      videoRef.current.currentTime = start;
      videoRef.current.play().catch(() => undefined);
    }
  }
  function toggle(id: string) {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }
  async function saveCorrection(verdict: "accurate" | "needs_correction") {
    setMessage("Saving a separate human-verification object to B2…");
    const fields = verdict === "needs_correction" ? {summary: draftSummary.trim()} : {};
    try {
      await apiFetch<Correction>(`/api/projects/${projectId}/scenes/${scene.id}/correction`, {
        method: "PUT", body: JSON.stringify({scene_id: scene.id, verdict, fields}),
      });
      setVerified((value) => ({...value, [scene.id]: verdict}));
      if (verdict === "needs_correction" && draftSummary.trim()) {
        setSceneList((items) => items.map((item) => item.id === scene.id ? {...item, summary: draftSummary.trim()} : item));
      }
      setEditing(false);
      setMessage("Human verification saved separately in B2 and will take precedence in future searches.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "The correction could not be saved.");
    }
  }
  async function generateBrief() {
    if (seeded) {
      router.push("/briefs/11111111-1111-4111-8111-111111111111?project=demo-coordinated-response");
      return;
    }
    setMessage("Checking for the one-time cached Genblaze brief…");
    try {
      const brief = await apiFetch<ApiBrief>("/api/briefs", {
        method: "POST", body: JSON.stringify({project_id: projectId, scene_ids: selected}),
      }, 240000);
      router.push(`/briefs/${brief.brief_id}?project=${projectId}`);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "The cached brief is not available.");
    }
  }

  const duration = Math.max(project.duration_seconds, sceneList.at(-1)?.end || 1);
  return (
    <div className="page video-page">
      <header className="video-header"><div><Link href="/">Library</Link><span>/</span><p>{project.seeded_demo ? "Seeded public demo" : "Backblaze B2 project"}</p><h1>{project.title}</h1><div className="video-submeta"><span>{project.exercise_type}</span><i /><span>{project.exercise_date}</span><i /><span><Database size={13} /> {project.storage === "b2" ? "Stored in B2" : "Public source"}</span></div></div><Link className="button secondary" href="/search"><Search size={16} /> Search library</Link></header>
      <section className="video-workspace">
        <div className="player-column">
          <div className="video-frame"><video ref={videoRef} controls preload="metadata" poster={project.thumbnail_url || undefined} onLoadedMetadata={seekFromUrl}><source src={project.video_url || undefined} type="video/mp4" /></video><span className="source-badge">{project.seeded_demo ? "SEEDED PUBLIC DEMO" : "PRIVATE B2 · SIGNED URL"}</span></div>
          <div className="timeline"><div className="timeline-labels"><span>00:00</span><span>{sceneList.at(-1)?.range.split("–")[1]}</span></div><div className="timeline-track">{sceneList.map((item) => <button key={item.id} className={item.id === active ? "active" : ""} style={{ width: `${((item.end - item.start) / duration) * 100}%` }} onClick={() => openScene(item.id, item.start)} aria-label={`Open ${item.range}`} />)}</div></div>
          <div className="source-note"><CircleAlert size={15} /><p><strong>Source:</strong> {project.source_attribution || "Synthetic or user-created exercise footage stored in the configured B2 bucket."} AARchive does not imply affiliation or government approval.</p></div>
        </div>
        <aside className="scene-inspector">
          <div className="inspector-top"><div><p className="eyebrow">Scene observation</p><h2>{scene.range}</h2></div><span className="confidence-ring">{scene.confidence}<small>%</small></span></div>
          <div className="machine-label"><Sparkles size={14} /> Machine-generated · human verification required</div>
          <h3>{scene.summary}</h3><blockquote>“{scene.excerpt}”</blockquote>
          {scene.positive && <div className="observation positive"><span>Observed positive behavior</span><p>{scene.positive}</p></div>}
          {scene.issue && <div className="observation issue"><span>Possible review point</span><p>{scene.issue}</p></div>}
          <div className="metadata-groups"><div><span>Activities</span><p>{scene.activities.join(" · ") || "Not observed"}</p></div><div><span>Roles</span><p>{scene.roles.join(" · ") || "Not observed"}</p></div><div><span>Equipment</span><p>{scene.equipment.join(" · ") || "Not observed"}</p></div><div><span>Environment</span><p>{scene.environment.join(" · ") || "Not observed"}</p></div></div>
          <div className="tag-row">{scene.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
          <div className="verify-controls"><p>Is this observation accurate?</p><div><button className={verified[scene.id] === "accurate" ? "selected" : ""} onClick={() => saveCorrection("accurate")}><Check size={15} /> Accurate</button><button className={editing ? "selected warning" : ""} onClick={() => { setEditing(true); setDraftSummary(scene.summary); }}><Edit3 size={15} /> Needs correction</button></div>{editing && <label><span>Corrected scene summary</span><textarea value={draftSummary} onChange={(event) => setDraftSummary(event.target.value)} rows={4} /><button onClick={() => saveCorrection("needs_correction")} disabled={!draftSummary.trim()}>Save correction</button></label>}<small>{message || "Original machine output remains unchanged; corrections are stored separately and take precedence."}</small></div>
        </aside>
      </section>
      <section className="scene-list-section"><div className="section-heading"><div><p className="eyebrow">Indexed timeline</p><h2>{sceneList.length} searchable scenes</h2></div><button className="plain-button">Transcript <ChevronDown size={15} /></button></div><div className="scene-table">{sceneList.map((item) => <div className={item.id === active ? "active" : ""} key={item.id}><button className={`scene-check ${selected.includes(item.id) ? "checked" : ""}`} onClick={() => toggle(item.id)} aria-label={`Select ${item.range}`}>{selected.includes(item.id) && <Check size={13} />}</button><button className="scene-time" onClick={() => openScene(item.id, item.start)}><Play size={12} fill="currentColor" /> {item.range}</button><button className="scene-summary" onClick={() => openScene(item.id, item.start)}>{item.summary}</button><span>{verified[item.id] || "unreviewed"}</span></div>)}</div></section>
      {selected.length > 0 && <div className="selection-bar"><div><strong>{selected.length} scenes selected</strong><span>{message || "Human review remains required."}</span></div><button className="button primary" onClick={generateBrief}><FileText size={16} /> Generate After-Action Brief</button></div>}
    </div>
  );
}
