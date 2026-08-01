"use client";

import { AlertCircle, ArrowRight, CheckCircle2, CloudUpload, FileVideo2, RotateCcw } from "lucide-react";
import Link from "next/link";
import { FormEvent, useRef, useState } from "react";
import { ApiProject, apiFetch } from "../lib/api";

const steps = ["Uploading", "Extracting", "Transcribing", "Analyzing scenes", "Indexing", "Ready"];

export function UploadForm() {
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<"idle" | "error" | "working" | "ready">("idle");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [project, setProject] = useState<ApiProject | null>(null);
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
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) { setError("Add an MP4 before starting the upload."); setState("error"); return; }
    const data = new FormData(event.currentTarget);
    setState("working");
    setError("");
    setStatusMessage("Requesting a short-lived B2 upload URL…");
    try {
      const ticket = await apiFetch<{
        project: ApiProject; upload_url: string; headers: Record<string, string>; object_key: string;
      }>("/api/uploads/presign", {
        method: "POST",
        body: JSON.stringify({
          title: data.get("title"),
          exercise_type: data.get("exercise_type"),
          exercise_date: data.get("exercise_date"),
          description: data.get("description") || null,
          filename: file.name,
          content_type: "video/mp4",
          size_bytes: file.size,
        }),
      });
      setProject(ticket.project);
      setStatusMessage(`Uploading ${file.name} directly to Backblaze B2…`);
      const uploaded = await fetch(ticket.upload_url, {method: "PUT", headers: ticket.headers, body: file});
      if (!uploaded.ok) throw new Error(`B2 rejected the upload (${uploaded.status})`);
      setStatusMessage("Upload stored. Starting FFmpeg and local Whisper processing…");
      await apiFetch(`/api/projects/${ticket.project.project_id}/process`, {method: "POST"});
      for (let attempt = 0; attempt < 450; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        const detail = await apiFetch<{project: ApiProject}>(`/api/projects/${ticket.project.project_id}`, undefined, 60000);
        setProject(detail.project);
        setStatusMessage(detail.project.status_message);
        if (detail.project.status === "ready") { setState("ready"); return; }
        if (detail.project.status === "failed") throw new Error(detail.project.status_message);
      }
      throw new Error("Processing is still running. Open the library shortly to check its durable status.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The upload could not be completed.");
      setState("error");
    }
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
          <label className="wide"><span>Video title</span><input name="title" required minLength={2} placeholder="e.g. North warehouse evacuation drill" /></label>
          <label><span>Exercise type</span><select name="exercise_type" required defaultValue=""><option value="" disabled>Select a type</option><option>Emergency response</option><option>Evacuation procedure</option><option>Team coordination</option><option>Instructor demonstration</option><option>Other</option></select></label>
          <label><span>Exercise date</span><input name="exercise_date" required type="date" /></label>
          <label className="wide"><span>Description <em>optional</em></span><textarea name="description" rows={4} placeholder="What scenario was being practiced? Do not include sensitive or classified information." /></label>
        </div>
        <div className="upload-consent"><CheckCircle2 size={17} /><span>I confirm this footage is public, synthetic, reenacted, or mine to upload.</span></div>
        <button className="button primary submit-upload" type="submit" disabled={state === "working"}>Upload to Backblaze B2 <ArrowRight size={17} /></button>
      </form>
      <aside className="process-panel">
        <p className="eyebrow">What happens next</p><h2>A visible, retryable pipeline.</h2><p>No step is marked complete until its output is durable.</p>
        <ol>{steps.map((step, index) => <li key={step}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{step}</strong><small>{["Browser sends bytes to a short-lived B2 URL", "FFmpeg creates temporary audio and frames", "Timestamped speech becomes source text", "Conservative scene metadata is proposed", "Corrected fields become searchable", "Media and JSON objects are available"][index]}</small></div></li>)}</ol>
        <div className="privacy-note"><strong>Private bucket friendly</strong><span>Video playback uses short-lived signed URLs. Provider and storage keys stay on the backend.</span></div>
      </aside>
      {(state === "working" || state === "ready") && <div className="modal-backdrop"><div className="state-modal"><div className="modal-icon">{state === "ready" ? <CheckCircle2 /> : <CloudUpload />}</div><p className="eyebrow">{state === "ready" ? "Stored and indexed" : "Durable processing"}</p><h2>{state === "ready" ? "Your searchable video is ready." : "Processing the B2 source object…"}</h2><p>{statusMessage}</p><div className="modal-actions">{state === "ready" && project ? <><button className="button secondary" onClick={() => { setState("idle"); setFile(null); }}><RotateCcw size={15} /> Upload another</button><Link className="button primary" href={`/videos/${project.project_id}`}>Open indexed video <ArrowRight size={15} /></Link></> : <Link className="button secondary" href="/">View library</Link>}</div></div></div>}
    </div>
  );
}
