"use client";

import Link from "next/link";
import { ArrowUpRight, CheckCircle2, Clock3, Database, FileAudio2, Layers3, Plus, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { SearchBox } from "./components/SearchBox";
import { StatusPill } from "./components/StatusPill";
import { projects as fallbackProjects, suggestedQueries } from "./lib/demo-data";
import { ApiProject, apiFetch, formatDuration } from "./lib/api";

type CardProject = {
  id: string; title: string; type: string; date: string; duration: string; status: string;
  scenes: number; briefs: number; thumbnail: string; storage: string; description: string; seeded: boolean;
};

export default function LibraryPage() {
  const [projects, setProjects] = useState<CardProject[]>(fallbackProjects.map((project) => ({
    ...project,
    storage: "Seeded demonstration",
    seeded: true,
  })));
  const [librarySource, setLibrarySource] = useState("Seeded demonstration · backend connection pending");

  useEffect(() => {
    apiFetch<ApiProject[]>("/api/projects", undefined, 60000).then((items) => {
      setProjects(items.map((project) => ({
        id: project.project_id,
        title: project.title,
        type: project.exercise_type,
        date: new Date(`${project.exercise_date}T00:00:00`).toLocaleDateString(undefined, {month: "short", day: "numeric", year: "numeric"}),
        duration: formatDuration(project.duration_seconds),
        status: project.status === "ready" ? "Ready" : project.status.replaceAll("_", " ").replace(/^./, (value) => value.toUpperCase()),
        scenes: project.indexed_scene_count,
        briefs: project.brief_count,
        thumbnail: project.thumbnail_url || "",
        storage: project.storage === "b2" ? "Stored in Backblaze B2" : "Seeded demonstration",
        description: project.description || "No description supplied.",
        seeded: project.seeded_demo,
      })));
      setLibrarySource("Connected to FastAPI · library metadata loaded from B2");
    }).catch(() => setLibrarySource("Seeded demonstration · backend unavailable"));
  }, []);

  const metrics = useMemo(() => ({
    videos: projects.length,
    scenes: projects.reduce((total, project) => total + project.scenes, 0),
    briefs: projects.reduce((total, project) => total + project.briefs, 0),
  }), [projects]);

  return (
    <div className="page library-page">
      <header className="page-header split-header">
        <div><p className="eyebrow">Training intelligence library</p><h1>Find the moment.<br /><span>Carry the lesson forward.</span></h1></div>
        <Link className="button primary" href="/upload"><Plus size={17} /> Add footage</Link>
      </header>

      <section className="hero-search">
        <div className="hero-search-heading"><Sparkles size={18} /><span>Search across transcripts, scene observations, and human corrections</span></div>
        <SearchBox />
        <div className="query-row"><span>Try</span>{suggestedQueries.map((query) => <Link key={query} href={`/search?q=${encodeURIComponent(query)}`}>{query}</Link>)}</div>
      </section>

      <section className="metric-strip" aria-label="Library statistics">
        <div><strong>{String(metrics.videos).padStart(2, "0")}</strong><span>training videos</span></div><i />
        <div><strong>{String(metrics.scenes).padStart(2, "0")}</strong><span>indexed scenes</span></div><i />
        <div><strong>{String(metrics.briefs).padStart(2, "0")}</strong><span>after-action briefs</span></div><i />
        <div className="b2-metric"><Database size={18} /><strong>B2</strong><span>durable object store</span></div>
      </section>

      <section className="section-block">
        <div className="section-heading"><div><p className="eyebrow">Your collection</p><h2>Training footage</h2></div><span className="muted">{librarySource}</span></div>
        <div className="project-grid">
          {projects.map((project, index) => (
            <article className={`project-card ${index === 0 ? "featured" : ""}`} key={project.id}>
              <div className={`project-image ${!project.thumbnail ? "placeholder-image" : ""}`} style={project.thumbnail ? { backgroundImage: `linear-gradient(180deg, transparent 35%, rgba(9,12,13,.88)), url("${project.thumbnail}")` } : undefined}>
                <div className="image-top"><StatusPill status={project.status} />{project.seeded && <span className="demo-label">SEEDED DEMO</span>}</div>
                <div className="image-bottom"><Clock3 size={14} /> {project.duration}</div>
              </div>
              <div className="project-body">
                <div className="project-type">{project.type}</div>
                <h3>{project.title}</h3>
                <p>{project.description}</p>
                <div className="project-meta"><span>{project.date}</span><span><Layers3 size={14} /> {project.scenes} scenes</span><span><FileAudio2 size={14} /> {project.briefs} briefs</span></div>
                <div className="card-footer"><span><Database size={13} /> {project.storage}</span>{project.status === "Ready" ? <Link href={`/videos/${project.id}`}>Open project <ArrowUpRight size={15} /></Link> : <span className="muted">Processing</span>}</div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="workflow-callout">
        <div className="workflow-copy"><p className="eyebrow">A simple evidence trail</p><h2>From raw footage to a reviewable brief.</h2><p>Every machine-generated observation stays linked to its source timestamp. Human corrections remain separate and take precedence in future search.</p></div>
        <div className="workflow-steps">
          {["Upload to B2", "Extract & organize", "Search exact moments", "Generate with Genblaze"].map((step, i) => <div key={step}><span>0{i + 1}</span><strong>{step}</strong>{i < 3 && <ArrowUpRight size={16} />}</div>)}
        </div>
        <div className="trust-note"><CheckCircle2 size={17} /><span>Designed for human review. No identity recognition, readiness scoring, or government-system claims.</span></div>
      </section>
    </div>
  );
}
