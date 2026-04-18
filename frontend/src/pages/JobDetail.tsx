import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { RecordRow } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { useJobPolling } from "../hooks/useJobPolling";
import { downloadCsv, recordsToCsv } from "../lib/csv";

const PAGE_SIZES = [10, 25, 50, 100];

export function JobDetail() {
  const { id } = useParams<{ id: string }>();
  const jobId = id ? Number(id) : null;
  const { job, error: jobError } = useJobPolling(jobId);

  const [records, setRecords] = useState<RecordRow[] | null>(null);
  const [hasNext, setHasNext] = useState(false);
  const [recordsError, setRecordsError] = useState<string | null>(null);
  const [filterDoc, setFilterDoc] = useState("");
  const [filterName, setFilterName] = useState("");
  const [filterSede, setFilterSede] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  const canLoad = job && (job.status === "done" || job.records_count > 0);

  // Reset to first page whenever filters or page size change
  useEffect(() => {
    setPage(1);
  }, [filterDoc, filterName, filterSede, pageSize]);

  useEffect(() => {
    if (!jobId || !canLoad) return;
    const controller = new AbortController();
    (async () => {
      try {
        const data = await api.listRecords(
          {
            job_id: jobId,
            patient_document: filterDoc || undefined,
            patient_name: filterName || undefined,
            sede: filterSede || undefined,
            skip: (page - 1) * pageSize,
            limit: pageSize + 1,
          },
          controller.signal
        );
        setHasNext(data.length > pageSize);
        setRecords(data.slice(0, pageSize));
        setRecordsError(null);
      } catch (e) {
        if (controller.signal.aborted) return;
        setRecordsError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => {
      controller.abort();
    };
  }, [jobId, canLoad, filterDoc, filterName, filterSede, page, pageSize]);

  const csvFilename = useMemo(
    () => (job ? `job_${job.id}_records_p${page}.csv` : `records_p${page}.csv`),
    [job, page]
  );

  function onDownload() {
    if (!records || records.length === 0) return;
    downloadCsv(csvFilename, recordsToCsv(records));
  }

  const rangeStart = records && records.length > 0 ? (page - 1) * pageSize + 1 : 0;
  const rangeEnd = records ? (page - 1) * pageSize + records.length : 0;

  if (!jobId) return <p>Job inválido.</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <Link to="/jobs" className="text-sm text-brand hover:underline">
            ← Jobs
          </Link>
          <h2 className="text-xl font-semibold">Job #{jobId}</h2>
        </div>
        {job && (
          <button
            onClick={onDownload}
            disabled={!records || records.length === 0}
            className="bg-brand hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded"
          >
            Descargar CSV (página actual)
          </button>
        )}
      </div>

      {jobError && <p className="text-sm text-status-error mb-3">{jobError}</p>}

      {job && (
        <div className="bg-white border border-gray-200 rounded-lg p-5 mb-6 shadow-sm">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <Field label="Estado">
              <StatusBadge status={job.status} />
            </Field>
            <Field label="Rango">
              {job.fecha_inicial} → {job.fecha_final}
            </Field>
            <Field label="Límite">{job.limit}</Field>
            <Field label="Registros">{job.records_count}</Field>
            <Field label="Creado">{fmt(job.created_at)}</Field>
            <Field label="Iniciado">{job.started_at ? fmt(job.started_at) : "—"}</Field>
            <Field label="Finalizado">{job.finished_at ? fmt(job.finished_at) : "—"}</Field>
          </div>
          {job.error_message && (
            <pre className="mt-4 bg-red-50 border border-red-200 text-red-800 text-xs p-3 rounded overflow-x-auto whitespace-pre-wrap">
              {job.error_message}
            </pre>
          )}
        </div>
      )}

      {canLoad && (
        <>
          <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-3">
            <FilterInput
              label="Documento"
              value={filterDoc}
              onChange={setFilterDoc}
              placeholder="Ej: 25232067"
            />
            <FilterInput
              label="Nombre"
              value={filterName}
              onChange={setFilterName}
              placeholder="Ej: OROZCO"
            />
            <FilterInput
              label="Sede"
              value={filterSede}
              onChange={setFilterSede}
              placeholder="Ej: La Mujer"
            />
          </div>

          {recordsError && <p className="text-sm text-status-error mb-3">{recordsError}</p>}

          {records === null ? (
            <p className="text-sm text-gray-500">Cargando registros…</p>
          ) : records.length === 0 ? (
            <p className="text-sm text-gray-500">Sin registros para estos filtros.</p>
          ) : (
            <>
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 text-gray-600">
                    <tr>
                      <Th>No. Orden</Th>
                      <Th>Documento</Th>
                      <Th>Nombre</Th>
                      <Th>Fecha cita</Th>
                      <Th>Sede</Th>
                      <Th>Contrato</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {records.map((r) => (
                      <tr key={r.id} className="hover:bg-gray-50">
                        <Td className="font-mono">{r.external_row_id ?? "—"}</Td>
                        <Td>{r.patient_document ?? "—"}</Td>
                        <Td>{r.patient_name ?? "—"}</Td>
                        <Td>{r.date_service ?? "—"}</Td>
                        <Td>{r.sede ?? "—"}</Td>
                        <Td>{r.contrato ?? "—"}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between mt-3 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <span>Filas por página:</span>
                  <select
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    className="border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
                  >
                    {PAGE_SIZES.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-3">
                  <span>
                    {rangeStart}–{rangeEnd} (página {page})
                  </span>
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Anterior
                  </button>
                  <button
                    onClick={() => setPage((p) => p + 1)}
                    disabled={!hasNext}
                    className="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    Siguiente
                  </button>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-0.5">{children}</div>
    </div>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-gray-600 mb-1">{label}</span>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded border-gray-300 border px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
      />
    </label>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return <th className="px-4 py-2 text-left font-medium whitespace-nowrap">{children}</th>;
}

function Td({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-2 ${className}`}>{children}</td>;
}

function fmt(iso: string): string {
  return new Date(iso).toLocaleString();
}
