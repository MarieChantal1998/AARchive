import { Suspense } from "react";
import { VideoDetail } from "./VideoDetail";

export default function VideoPage() { return <Suspense fallback={<div className="page">Loading indexed footage…</div>}><VideoDetail /></Suspense>; }

