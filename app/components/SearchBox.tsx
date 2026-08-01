"use client";

import { ArrowRight, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

export function SearchBox({ initial = "", compact = false }: { initial?: string; compact?: boolean }) {
  const [query, setQuery] = useState(initial);
  const router = useRouter();
  function submit(event: FormEvent) {
    event.preventDefault();
    if (query.trim()) router.push(`/search?q=${encodeURIComponent(query.trim())}`);
  }
  return (
    <form className={`search-box ${compact ? "compact" : ""}`} onSubmit={submit}>
      <Search size={21} aria-hidden="true" />
      <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search what happened, not which file it was in…" aria-label="Search training footage" />
      <button className="search-submit" aria-label="Run search"><span>Search moments</span><ArrowRight size={17} /></button>
    </form>
  );
}

