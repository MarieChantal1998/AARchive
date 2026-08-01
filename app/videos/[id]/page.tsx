import { Suspense } from "react";
import { VideoDetail } from "./VideoDetail";

export default async function VideoPage({params}: {params: Promise<{id: string}>}) {
  const {id} = await params;
  return <Suspense fallback={<div className="page">Loading indexed footage…</div>}><VideoDetail projectId={id} /></Suspense>;
}
