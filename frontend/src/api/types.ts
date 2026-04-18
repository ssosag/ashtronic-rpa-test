export type JobStatus = "queued" | "running" | "done" | "error";

export interface Job {
  id: number;
  status: JobStatus;
  fecha_inicial: string;
  fecha_final: string;
  limit: number;
  started_at: string | null;
  finished_at: string | null;
  records_count: number;
  error_message: string | null;
  created_at: string;
}

export interface RecordRow {
  id: number;
  job_id: number;
  external_row_id: string | null;
  patient_name: string | null;
  patient_document: string | null;
  date_service: string | null;
  sede: string | null;
  contrato: string | null;
  captured_at: string;
}

export interface RecordDetail extends RecordRow {
  raw_row_json: Record<string, string>;
}

export interface ExtractRequest {
  fecha_inicial: string;
  fecha_final: string;
  limit: number;
}

export interface ExtractResponse {
  job_id: number;
  status: string;
  message: string;
}

export interface RecordFilters {
  job_id?: number;
  patient_document?: string;
  patient_name?: string;
  sede?: string;
  skip?: number;
  limit?: number;
}
