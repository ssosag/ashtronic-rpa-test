import type { JobStatus } from "../api/types";

const STYLES: Record<JobStatus, string> = {
  queued: "bg-status-queued/15 text-yellow-700 ring-status-queued/40",
  running: "bg-status-running/15 text-sky-700 ring-status-running/40",
  done: "bg-status-done/15 text-green-700 ring-status-done/40",
  error: "bg-status-error/15 text-red-700 ring-status-error/40",
};

const LABEL: Record<JobStatus, string> = {
  queued: "En cola",
  running: "En curso",
  done: "Completado",
  error: "Error",
};

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STYLES[status]}`}
    >
      {LABEL[status]}
    </span>
  );
}
