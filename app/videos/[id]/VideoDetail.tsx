"use client";

import Link from "next/link";
import { Check, ChevronDown, CircleAlert, Database, Edit3, FileText, Play, Search, Sparkles } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { DEMO_VIDEO_URL, scenes } from "../../lib/demo-data";

export function VideoDetail() {
  const params = useSearchParams();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [active, setActive] = useState(params.get("scene") || scenes[0].id);
  const [selected, setSelected] = useState<string[]>([]);
  const [verified, setVerified] = useState<Record<string, string>>({});
  const scene = scenes.find((item) => item.id === active) || scenes[0];
  useEffect(() => {
    const start = Number(params.get("t") || 0);
    if (videoRef.current && Number.isFinite(start)) videoRef.current.currentTime = start;
  }, [params]);
  function openScene(id: string, start: number) { setActive(id); if (videoRef.current) { videoRef.current.currentTime = start; videoRef.current.play().catch(() => undefined); } }
  function toggle(id: string) { setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); }
  return (
    <div className="page video-page">
      <header className="video-header"><div><Link href="/">Library</Link><span>/</span><p>Public demo</p><h1>Integrated Emergency Response Exercise</h1><div className="video-submeta"><span>Emergency response / triage</span><i /><span>Apr 29, 2026</span><i /><span><Database size={13} /> Public source · B2-ready</span></div></div><Link className="button secondary" href="/search"><Search size={16} /> Search library</Link></header>
      <section className="video-workspace">
        <div className="player-column">
          <div className="video-frame"><video ref={videoRef} controls preload="metadata" poster="https://upload.wikimedia.org/wikipedia/commons/thumb/7/78/USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm/960px--USAG-Italy_DES_Integrated_Emergency_Exercise_%281008879%29.webm.jpg"><source src={DEMO_VIDEO_URL} type="video/mp4" /></video><span className="source-badge">PUBLIC-DOMAIN DEMO</span></div>
          <div className="timeline"><div className="timeline-labels"><span>00:00</span><span>00:57</span></div><div className="timeline-track">{scenes.map((item) => <button key={item.id} className={item.id === active ? "active" : ""} style={{ width: `${((item.end - item.start) / 57) * 100}%` }} onClick={() => openScene(item.id, item.start)} aria-label={`Open ${item.range}`} />)}</div></div>
          <div className="source-note"><CircleAlert size={15} /><p><strong>Source:</strong> public-domain U.S. Army exercise footage via Wikimedia Commons / DVIDS. AARchive is not affiliated with the source organization.</p></div>
        </div>
        <aside className="scene-inspector">
          <div className="inspector-top"><div><p className="eyebrow">Scene observation</p><h2>{scene.range}</h2></div><span className="confidence-ring">{scene.confidence}<small>%</small></span></div>
          <div className="machine-label"><Sparkles size={14} /> Machine-generated · human verification required</div>
          <h3>{scene.summary}</h3><blockquote>“{scene.excerpt}”</blockquote>
          {scene.positive && <div className="observation positive"><span>Observed positive behavior</span><p>{scene.positive}</p></div>}
          {scene.issue && <div className="observation issue"><span>Possible review point</span><p>{scene.issue}</p></div>}
          <div className="metadata-groups"><div><span>Activities</span><p>{scene.activities.join(" · ")}</p></div><div><span>Roles</span><p>{scene.roles.join(" · ")}</p></div><div><span>Equipment</span><p>{scene.equipment.join(" · ")}</p></div><div><span>Environment</span><p>{scene.environment.join(" · ")}</p></div></div>
          <div className="tag-row">{scene.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
          <div className="verify-controls"><p>Is this observation accurate?</p><div><button className={verified[scene.id] === "accurate" ? "selected" : ""} onClick={() => setVerified((value) => ({ ...value, [scene.id]: "accurate" }))}><Check size={15} /> Accurate</button><button className={verified[scene.id] === "correction" ? "selected warning" : ""} onClick={() => setVerified((value) => ({ ...value, [scene.id]: "correction" }))}><Edit3 size={15} /> Needs correction</button></div><small>{verified[scene.id] ? "Demo-only review state. Connect B2 to persist a separate correction object." : "Original AI output remains unchanged when corrections are saved."}</small></div>
        </aside>
      </section>
      <section className="scene-list-section"><div className="section-heading"><div><p className="eyebrow">Indexed timeline</p><h2>5 searchable scenes</h2></div><button className="plain-button">Transcript <ChevronDown size={15} /></button></div><div className="scene-table">{scenes.map((item) => <div className={item.id === active ? "active" : ""} key={item.id}><button className={`scene-check ${selected.includes(item.id) ? "checked" : ""}`} onClick={() => toggle(item.id)} aria-label={`Select ${item.range}`}>{selected.includes(item.id) && <Check size={13} />}</button><button className="scene-time" onClick={() => openScene(item.id, item.start)}><Play size={12} fill="currentColor" /> {item.range}</button><button className="scene-summary" onClick={() => openScene(item.id, item.start)}>{item.summary}</button><span>{verified[item.id] || "unreviewed"}</span></div>)}</div></section>
      {selected.length > 0 && <div className="selection-bar"><div><strong>{selected.length} scenes selected</strong><span>Human review remains required.</span></div><Link className="button primary" href={`/briefs/11111111-1111-4111-8111-111111111111?scenes=${selected.join(",")}`}><FileText size={16} /> Generate After-Action Brief</Link></div>}
    </div>
  );
}

