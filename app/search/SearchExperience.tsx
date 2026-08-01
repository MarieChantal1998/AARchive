"use client";

import Link from "next/link";
import { ArrowRight, CheckSquare2, Filter, Play, Sparkles, Square } from "lucide-react";
import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { SearchBox } from "../components/SearchBox";
import { scenes, searchScenes, suggestedQueries } from "../lib/demo-data";

export function SearchExperience() {
  const params = useSearchParams();
  const query = params.get("q") || "effective team coordination";
  const [selected, setSelected] = useState<string[]>([]);
  const [tag, setTag] = useState("All tags");
  const results = useMemo(() => {
    const ranked = searchScenes(query);
    const fallback = ranked.length ? ranked : scenes.map((scene) => ({ scene, matched: [], score: 1 }));
    return tag === "All tags" ? fallback : fallback.filter((item) => item.scene.tags.includes(tag));
  }, [query, tag]);
  const allTags = ["All tags", "coordination", "triage", "handoff", "transport"];
  function toggle(id: string) {
    setSelected((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
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
      <div className="results-heading"><div><p className="eyebrow">Ranked results</p><h2>{results.length} moments for “{query}”</h2></div><span className="ai-observation"><Sparkles size={14} /> Machine observations · verify before use</span></div>
      <div className="results-list">
        {results.map(({ scene, matched }, index) => {
          const checked = selected.includes(scene.id);
          return (
            <article className="result-card" key={scene.id}>
              <button className="select-scene" onClick={() => toggle(scene.id)} aria-label={`${checked ? "Deselect" : "Select"} ${scene.range}`}>{checked ? <CheckSquare2 /> : <Square />}</button>
              <div className="rank">{String(index + 1).padStart(2, "0")}</div>
              <div className="result-content">
                <div className="result-kicker"><span>Integrated Emergency Response Exercise</span><strong>{scene.range}</strong></div>
                <h3>{scene.summary}</h3>
                <blockquote>“{scene.excerpt}”</blockquote>
                <div className="tag-row">{scene.tags.map((item) => <span className={matched.includes(item) ? "matched" : ""} key={item}>{item}</span>)}</div>
              </div>
              <div className="result-actions"><span className="relevance"><i style={{ width: `${scene.confidence}%` }} />{scene.confidence}% observation confidence</span><Link className="button secondary" href={`/videos/demo-coordinated-response?t=${scene.start}&scene=${scene.id}`}><Play size={15} fill="currentColor" /> Open moment</Link></div>
            </article>
          );
        })}
      </div>
      {selected.length > 0 && <div className="selection-bar"><div><strong>{selected.length} scene{selected.length > 1 ? "s" : ""} selected</strong><span>Source timestamps will be carried into the brief.</span></div><Link className="button primary" href={`/briefs/11111111-1111-4111-8111-111111111111?scenes=${selected.join(",")}`}>Generate After-Action Brief <ArrowRight size={16} /></Link></div>}
      <div className="query-suggestions"><span>Other searches</span>{suggestedQueries.map((item) => <Link key={item} href={`/search?q=${encodeURIComponent(item)}`}>{item}</Link>)}</div>
    </div>
  );
}

