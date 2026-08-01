import { Check, LoaderCircle } from "lucide-react";

export function StatusPill({ status }: { status: string }) {
  const ready = status === "Ready";
  return <span className={`status-pill ${ready ? "ready" : "working"}`}>{ready ? <Check size={12} /> : <LoaderCircle size={12} />} {status}</span>;
}

