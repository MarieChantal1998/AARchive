import Link from "next/link";
import Image from "next/image";
import { AlertTriangle, ArrowLeft, Calendar, CheckCircle2, ChevronDown, Clock3, Copy, Database, ExternalLink, FileJson2, PlayCircle, ShieldCheck, Sparkles, Volume2 } from "lucide-react";

export default function BriefPage() {
  return (
    <div className="page brief-page">
      <div className="brief-back"><Link href="/videos/demo-coordinated-response"><ArrowLeft size={15} /> Back to source video</Link><span>Seeded demonstration brief</span></div>
      <header className="brief-header">
        <div><p className="eyebrow">After-action brief · AAR-001</p><h1>Coordinated Triage-to-Transport Handoff</h1><p>Generated from selected, timestamped observations in the Integrated Emergency Response Exercise.</p><div className="brief-meta"><span><Calendar size={14} /> Jul 31, 2026</span><span><Clock3 size={14} /> 00:20–00:45</span><span><Database size={14} /> Demo cache · B2-ready</span></div></div>
        <span className="verification-badge unverified"><AlertTriangle size={15} /> Seeded asset · manifest not verified</span>
      </header>
      <div className="brief-grid">
        <main className="brief-document">
          <div className="brief-cover"><Image src="/demo-brief-cover.png" width={1536} height={1024} priority alt="AARchive after-action brief cover with a searchable media timeline" /><span>AI-created seeded cover · generated outside the live Genblaze endpoint</span></div>
          <section className="audio-card"><div className="audio-icon"><Volume2 /></div><div><span>Narrated briefing · 00:35</span><audio controls preload="metadata"><source src="/demo-narration.mp3" type="audio/mpeg" /></audio><small>Bundled synthetic narration for judge-ready playback. Live generation uses Genblaze + OpenAI TTS and persists the manifest to B2.</small></div></section>
          <div className="review-banner"><ShieldCheck size={18} /><p><strong>Human review required.</strong> This brief was generated from selected footage observations. A qualified reviewer should confirm the source moments and all conclusions before reuse.</p></div>
          <section className="brief-section"><span className="section-index">01</span><div><p className="eyebrow">Situation summary</p><h2>A structured response moved from arrival and triage into casualty transport.</h2><p>Responders established a working area, assessed simulated casualties, and coordinated movement from the triage area to transport. The selected sequence focuses on the observable handoff between medical and transport roles.</p></div></section>
          <section className="brief-section"><span className="section-index">02</span><div><p className="eyebrow">What occurred</p><ul className="brief-list"><li>Medical personnel performed triage while preparing a simulated casualty for movement.</li><li>The transport team aligned with field responders around a stretcher movement and vehicle handoff.</li><li>The transition point appeared briefly congested before the route cleared and movement resumed.</li></ul></div></section>
          <div className="two-column-brief"><section><p className="eyebrow positive-text">Observed positive behaviors</p><h3>Coordination continued through friction.</h3><p>Responders worked in parallel during triage and recovered from brief congestion without abandoning the handoff sequence.</p></section><section><p className="eyebrow amber-text">Improvement opportunity</p><h3>Clarify the movement route earlier.</h3><p>Review route-clearance ownership and the exact handoff wording before movement begins.</p></section></div>
          <section className="brief-section questions"><span className="section-index">03</span><div><p className="eyebrow">Suggested discussion questions</p><ol><li><span>01</span>Which details should be confirmed before a stretcher leaves the triage area?</li><li><span>02</span>How could the transition point remain clear during simultaneous operations?</li><li><span>03</span>What observable evidence would show that the adjustment worked next time?</li></ol></div></section>
          <section className="sources-section"><div className="section-heading"><div><p className="eyebrow">Source evidence</p><h2>Linked timestamps</h2></div><Link href="/videos/demo-coordinated-response?t=20&scene=scene-003">Open full video <ExternalLink size={14} /></Link></div><Link className="source-row" href="/videos/demo-coordinated-response?t=20&scene=scene-003"><PlayCircle /><span><strong>00:20–00:32</strong><small>Triage preparation</small></span><p>Medical personnel prepare a simulated casualty for movement.</p></Link><Link className="source-row" href="/videos/demo-coordinated-response?t=32.5&scene=scene-004"><PlayCircle /><span><strong>00:32–00:45</strong><small>Transport handoff</small></span><p>Field responders coordinate the transition to transport.</p></Link></section>
        </main>
        <aside className="provenance-panel">
          <div className="provenance-heading"><Sparkles size={18} /><div><p className="eyebrow">Generation record</p><h2>Provenance</h2></div></div>
          <div className="provider-stack"><span>Live pipeline provider</span><strong>OpenAI via Genblaze</strong><small>Seeded media is explicitly unverified</small></div>
          <dl><div><dt>Pipeline</dt><dd>aarchive-after-action-brief</dd></div><div><dt>Image model</dt><dd>gpt-image-1</dd></div><div><dt>Audio model</dt><dd>gpt-4o-mini-tts</dd></div><div><dt>Storage sink</dt><dd>Backblaze B2 / S3</dd></div><div><dt>Key strategy</dt><dd>Hierarchical</dd></div><div><dt>Manifest hash</dt><dd className="hash-value">Not available for seeded preview</dd></div><div><dt>Verification</dt><dd className="unverified-text">Not generated by live endpoint</dd></div></dl>
          <button className="provenance-toggle"><FileJson2 size={16} /> Useful manifest fields <ChevronDown size={15} /></button>
          <div className="manifest-preview"><code>{`{
  "pipeline": "aarchive-after-action-brief",
  "provider": "openai",
  "storage": "backblaze-b2",
  "verification": "not_generated"
}`}</code><button aria-label="Copy provenance"><Copy size={14} /></button></div>
          <div className="provenance-note"><CheckCircle2 size={16} /><p>The live endpoint stores generated assets and canonical Genblaze manifests together in B2. Secrets and private prompts are never returned.</p></div>
        </aside>
      </div>
    </div>
  );
}
