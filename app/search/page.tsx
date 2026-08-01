import { Suspense } from "react";
import { SearchExperience } from "./SearchExperience";

export default function SearchPage() {
  return <Suspense fallback={<div className="page"><p>Preparing search…</p></div>}><SearchExperience /></Suspense>;
}

