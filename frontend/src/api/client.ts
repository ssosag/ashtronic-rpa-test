import type {
  ExtractRequest,
  ExtractResponse,
  Job,
  RecordRow,
  RecordDetail,
  RecordFilters,
} from "./types";

const BASE = "/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = formatDetail(body.detail) ?? JSON.stringify(body);
    } catch {
      // leave statusText
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function formatDetail(detail: unknown): string | null {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation errors: [{loc: [...], msg: "...", type: "..."}, ...]
    return detail
      .map((err) => {
        if (typeof err === "string") return err;
        if (err && typeof err === "object" && "msg" in err) {
          const loc = Array.isArray((err as { loc?: unknown[] }).loc)
            ? (err as { loc: unknown[] }).loc.slice(1).join(".") // skip "body"
            : "";
          const msg = (err as { msg: string }).msg;
          return loc ? `${loc}: ${msg}` : msg;
        }
        return JSON.stringify(err);
      })
      .join("; ");
  }
  return JSON.stringify(detail);
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== "" && v !== null
  );
  if (entries.length === 0) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of entries) sp.set(k, String(v));
  return `?${sp.toString()}`;
}

export const api = {
  extract: (body: ExtractRequest) =>
    request<ExtractResponse>("/rpa/extract", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  listJobs: (skip = 0, limit = 50) =>
    request<Job[]>(`/jobs${qs({ skip, limit })}`),

  getJob: (id: number) => request<Job>(`/jobs/${id}`),

  listRecords: (filters: RecordFilters = {}) =>
    request<RecordRow[]>(`/records${qs({ ...filters, limit: filters.limit ?? 100 })}`),

  getRecord: (id: number) => request<RecordDetail>(`/records/${id}`),
};

export { ApiError };
