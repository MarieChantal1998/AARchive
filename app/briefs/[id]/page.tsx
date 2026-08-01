/* eslint-disable @next/next/no-img-element -- B2 URLs are short-lived signed URLs. */
"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AlertTriangle, ArrowLeft, Calendar, CheckCircle2, ChevronDown, Clock3, Copy, Database, ExternalLink, FileJson2, PlayCircle, ShieldCheck, Sparkles, Volume2 } from "lucide-react";
import { ApiBrief, apiFetch } from "../../lib/api";

const seededBrief: ApiBrief = {
  brief_id: "11111111-1111-4111-8111-111111111111",
  project_id: "demo-coordinated-response",
  title: "Coordinated Triage-to-Transport Handoff",
  situation_summary: "A structured response moved from arrival and triage into casualty transport.",
  what_occurred: [
    "Medical personnel performed triage while preparing a simulated casualty for movement.",
    "The transport team aligned with field responders around a stretcher movement and vehicle handoff.",
    "The transition point appeared briefly congested before the route cleared and movement resumed.",
  ],
  positive_behaviors: ["Responders worked in parallel and recovered from brief congestion without abandoning the handoff."],
  improvement_opportunity: "Review route-clearance ownership and the exact handoff wording before movement begins.",
  discussion_questions: [
    "Which details should be confirmed before a stretcher leaves the triage area?",
    "How could the transition point remain clear during simultaneous operations?",
    "What observable evidence would show that the adjustment worked next time?",
  ],
  source_timestamps: [
    {scene_id: "scene-003", label: "Triage preparation", start_seconds: 20, timestamp: "00:20–00:32"},
    {scene_id: "scene-004", label: "Transport handoff", start_seconds: 32.5, timestamp: "00:32–00:45"},
  ],
  review_notice: "This seeded demonstration brief must be reviewed by a qualified human.",
  cover_url: "/demo-brief-cover.png",
  narration_url: "/demo-narration.mp3",
  provider: "Seeded demonstration · not a verified Genblaze run",
  models: [], generated_at: "2026-07-31T00:00:00Z", manifest_hash: null, manifest_uri: null,
  verification_status: "not_generated",
  provenance: {pipeline: "not_run", storage: "bundled_seeded_asset", verification: "not_generated"},
  seeded_demo: true,
};

export default function BriefPage() {
  const route = useParams<{id: string}>();
  const search = useSearchParams();
  const projectId = search.get("project") || "demo-coordinated-response";
  const [brief, setBrief] = useState<ApiBrief>(seededBrief);
  const [status, setStatus] = useState("Seeded demonstration · manifest not verified");

  useEffect(() => {
    apiFetch<ApiBrief>(`/api/projects/${projectId}/briefs/${route.id}`, undefined, 60000).then((value) => {
      setBrief(value);
      setStatus(value.seeded_demo ? "Seeded demonstration · manifest not verified" : "Previously generated demonstration · loaded from B2");
    }).catch(() => {
      if (route.id !== seededBrief.brief_id) setStatus("This B2 brief is not available.");
    });
  }, [projectId, route.id]);

  const verified = brief.verification_status === "verified" && Boolean(brief.manifest_hash);
  const date = new Date(brief.generated_at).toLocaleDateString(undefined, {month: "short", day: "numeric", year: "numeric"});
  const provenance = JSON.stringify(brief.provenance, null, 2);
  return (
    <div className="page brief-page">
      <div className="brief-back"><Link href={`/videos/${brief.project_id}`}><ArrowLeft size={15} /> Back to source video</Link><span>{status}</span></div>
      <header className="brief-header">
        <div><p className="eyebrow">After-action brief</p><h1>{brief.title}</h1><p>{brief.situation_summary}</p><div className="brief-meta"><span><Calendar size={14} /> {date}</span><span><Clock3 size={14} /> {brief.source_timestamps.map((item) => item.timestamp).join(" · ")}</span><span><Database size={14} /> {brief.seeded_demo ? "Seeded asset" : "Backblaze B2"}</span></div></div>
        <span className={`verification-badge ${verified ? "" : "unverified"}`}><AlertTriangle size={15} /> {verified ? "Genblaze manifest verified" : "Manifest not verified"}</span>
      </header>
      <div className="brief-grid">
        <main className="brief-document">
          {brief.cover_url && <div className="brief-cover">{/* Signed B2 URLs are intentionally not sent through an image optimizer. */}<img src={brief.cover_url} width={1536} height={1024} alt="AARchive after-action briefing cover" /><span>{verified ? "Previously generated Genblaze cover · cached in B2" : "Seeded cover · not a verified Genblaze output"}</span></div>}
          {brief.narration_url && <section className="audio-card"><div className="audio-icon"><Volume2 /></div><div><span>Narrated briefing</span><audio controls preload="metadata"><source src={brief.narration_url} /></audio><small>{verified ? "Previously generated narration loaded from B2; playback does not trigger inference." : "Seeded synthetic narration; no live generation is claimed."}</small></div></section>}
          <div className="review-banner"><ShieldCheck size={18} /><p><strong>Human review required.</strong> {brief.review_notice}</p></div>
          <section className="brief-section"><span className="section-index">01</span><div><p className="eyebrow">Situation summary</p><h2>{brief.situation_summary}</h2></div></section>
          <section className="brief-section"><span className="section-index">02</span><div><p className="eyebrow">What occurred</p><ul className="brief-list">{brief.what_occurred.map((item) => <li key={item}>{item}</li>)}</ul></div></section>
          <div className="two-column-brief"><section><p className="eyebrow positive-text">Observed positive behaviors</p><h3>Machine observations for discussion</h3><p>{brief.positive_behaviors.join(" ") || "No positive behavior was supported by the selected transcript."}</p></section><section><p className="eyebrow amber-text">Improvement opportunity</p><h3>Review with a qualified human</h3><p>{brief.improvement_opportunity}</p></section></div>
          <section className="brief-section questions"><span className="section-index">03</span><div><p className="eyebrow">Suggested discussion questions</p><ol>{brief.discussion_questions.map((item, index) => <li key={item}><span>{String(index + 1).padStart(2, "0")}</span>{item}</li>)}</ol></div></section>
          <section className="sources-section"><div className="section-heading"><div><p className="eyebrow">Source evidence</p><h2>Linked timestamps</h2></div><Link href={`/videos/${brief.project_id}`} >Open full video <ExternalLink size={14} /></Link></div>{brief.source_timestamps.map((item) => <Link className="source-row" key={item.scene_id} href={`/videos/${brief.project_id}?t=${item.start_seconds}&scene=${item.scene_id}`}><PlayCircle /><span><strong>{item.timestamp}</strong><small>{item.scene_id}</small></span><p>{item.label}</p></Link>)}</section>
        </main>
        <aside className="provenance-panel">
          <div className="provenance-heading"><Sparkles size={18} /><div><p className="eyebrow">Generation record</p><h2>Provenance</h2></div></div>
          <div className="provider-stack"><span>Recorded provider</span><strong>{brief.provider}</strong><small>{brief.seeded_demo ? "Seeded media is explicitly unverified" : "One-time generated media cached in B2"}</small></div>
          <dl><div><dt>Pipeline</dt><dd>{String(brief.provenance.pipeline || "Not recorded")}</dd></div><div><dt>Image model</dt><dd>{brief.models[0] || "Not generated"}</dd></div><div><dt>Audio model</dt><dd>{brief.models[1] || "Not generated"}</dd></div><div><dt>Storage sink</dt><dd>{String(brief.provenance.storage_sink || "Seeded bundle")}</dd></div><div><dt>Manifest hash</dt><dd className="hash-value">{brief.manifest_hash || "Not available"}</dd></div><div><dt>Verification</dt><dd className={verified ? "" : "unverified-text"}>{brief.verification_status}</dd></div></dl>
          <button className="provenance-toggle"><FileJson2 size={16} /> Useful manifest fields <ChevronDown size={15} /></button>
          <div className="manifest-preview"><code>{provenance}</code><button aria-label="Copy provenance" onClick={() => navigator.clipboard?.writeText(provenance)}><Copy size={14} /></button></div>
          <div className="provenance-note"><CheckCircle2 size={16} /><p>{verified ? "The canonical Genblaze manifest and generated assets are persisted in B2." : "No Genblaze run is claimed for this seeded output. Secrets and private prompts are never returned."}</p></div>
        </aside>
      </div>
    </div>
  );
}
