import type { RecordRow } from "../api/types";

const HEADERS: { key: keyof RecordRow; label: string }[] = [
  { key: "id", label: "id" },
  { key: "job_id", label: "job_id" },
  { key: "external_row_id", label: "no_orden" },
  { key: "patient_document", label: "documento" },
  { key: "patient_name", label: "nombres" },
  { key: "date_service", label: "fecha_cita" },
  { key: "sede", label: "sede" },
  { key: "contrato", label: "contrato" },
  { key: "captured_at", label: "captured_at" },
];

function escapeCell(value: unknown): string {
  if (value === null || value === undefined) return "";
  const s = String(value);
  if (/[",\n\r]/.test(s)) return `"${s.replace(/"/g, '""')}"`;
  return s;
}

export function recordsToCsv(rows: RecordRow[]): string {
  const head = HEADERS.map((h) => h.label).join(",");
  const body = rows
    .map((r) => HEADERS.map((h) => escapeCell(r[h.key])).join(","))
    .join("\n");
  return `${head}\n${body}`;
}

export function downloadCsv(filename: string, csv: string): void {
  // UTF-8 BOM so Excel opens it with correct encoding
  const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
