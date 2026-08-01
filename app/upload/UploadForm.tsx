"use client";

import { AlertCircle, ArrowRight, CheckCircle2, CloudUpload, FileVideo2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { FormEvent, useRef, useState } from "react";

const steps = ["Uploading", "Extracting", "Transcribing", "Analyzing scenes", "Indexing", "Ready"];

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<"idle" | "error" | "submitted">("idle");
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);
  function choose(next: File | undefined) {
    setError("");
    setState("idle");
    if (!next) return;
    if (next.type !== "video/mp4" && !next.name.toLowerCase().endsWith(".mp4")) {
      setError("Choose an MP4 file. Other formats are not uploaded."); setState("error"); return;
    }
    if (next.size > 500 * 1024 * 1024) {
      setError("This file is larger than the 500 MB MVP limit."); setState("error"); return;
    }
    setFile(next);
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) { setError("Add an MP4 before starting the upload."); setState("error"); return; }
    setState("submitted");
  }
  return (
    <div className="upload-layout">
      <form className="upload-panel" onSubmit={submit}>
        <div className="form-section"><span className="step-number">01</span><div><h2>Source footage</h2><p>MP4 only · up to 500 MB for this prototype</p></div></div>
        <button type="button" className={`dropzone ${file ? "has-file" : ""}`} onClick={() => inputRef.current?.click()} onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files[0]); }}>
          <input ref={inputRef} type="file" accept="video/mp4,.mp4" hidden onChange={(event) => choose(event.target.files?.[0])} />
          {file ? <><FileVideo2 size={30} /><strong>{file.name}</strong><span>{(file.size / 1024 / 1024).toFixed(1)} MB · ready for direct B2 upload</span></> : <><CloudUpload size={32} /><strong>Drop an MP4 here</strong><span>or click to choose from your device</span></>}
        </button>
        {error && <div className="form-error"><AlertCircle size={16} />{error}</div>}
        <div className="form-section metadata-title"><span className="step-number">02</span><div><h2>Exercise metadata</h2><p>Keep the title recognizable to the people who ran it.</p></div></div>
        <div className="field-grid">
          <label className="wide"><span>Video title</span><input required minLength={2} placeholder="e.g. North warehouse evacuation drill" /></label>
          <label><span>Exercise type</span><select required defaultValue=""><option value="" disabled>Select a type</option><option>Emergency response</option><option>Evacuation procedure</option><option>Team coordination</option><option>Instructor demonstration</option><option>Other</option></select></label>
          <label><span>Exercise date</span><input required type="date" /></label>
          <label className="wide"><span>Description <em>optional</em></span><textarea rows={4} placeholder="What scenario was being practiced? Do not include sensitive or classified information." /></label>
        </div>
        <div className="upload-consent"><CheckCircle2 size={17} /><span>I confirm this footage is public, synthetic, reenacted, or mine to upload.</span></div>
        <button className="button primary submit-upload" type="submit">Upload to Backblaze B2 <ArrowRight size={17} /></button>
      </form>
      <aside className="process-panel">
        <p className="eyebrow">What happens next</p><h2>A visible, retryable pipeline.</h2><p>No step is marked complete until its output is durable.</p>
        <ol>{steps.map((step, index) => <li key={step}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{step}</strong><small>{["Browser sends bytes to a short-lived B2 URL", "FFmpeg creates temporary audio and frames", "Timestamped speech becomes source text", "Conservative scene metadata is proposed", "Corrected fields become searchable", "Media and JSON objects are available"][index]}</small></div></li>)}</ol>
        <div className="privacy-note"><strong>Private bucket friendly</strong><span>Video playback uses short-lived signed URLs. Provider and storage keys stay on the backend.</span></div>
      </aside>
      {state === "submitted" && <div className="modal-backdrop"><div className="state-modal"><div className="modal-icon"><CloudUpload /></div><p className="eyebrow">Upload handoff</p><h2>Frontend flow is ready.</h2><p>This deployment has no cloud credentials embedded. Configure the backend environment to issue a real presigned B2 URL; until then, no upload is falsely marked successful.</p><div className="modal-actions"><button className="button secondary" onClick={() => setState("idle")}><RotateCcw size={15} /> Return to form</button><Link className="button primary" href="/">View seeded demo <ArrowRight size={15} /></Link></div></div></div>}
    </div>
  );
}
