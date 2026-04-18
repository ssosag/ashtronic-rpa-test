import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { RecordRow } from "../api/types";
import { downloadCsv, recordsToCsv } from "../lib/csv";

const PAGE_SIZES = [10, 25, 50, 100];

export function RecordsList() {
  const [records, setRecords] = useState<RecordRow[] | null>(null);
  const [hasNext, setHasNext] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [jobIdFilter, setJobIdFilter] = useState("");
  const [docFilter, setDocFilter] = useState("");
  const [nameFilter, setNameFilter] = useState("");
  const [sedeFilter, setSedeFilter] = useState("");

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);

  // Reset to first page whenever filters or page size change
  useEffect(() => {
    setPage(1);
  }, [jobIdFilter, docFilter, nameFilter, sedeFilter, pageSize]);

  useEffect(() => {
    const controller = new AbortController();
    const t = setTimeout(async () => {
      try {
        // Fetch one extra row to detect if there is a next page
        const data = await api.listRecords(
          {
            job_id: jobIdFilter ? Number(jobIdFilter) : undefined,
            patient_document: docFilter || undefined,
            patient_name: nameFilter || undefined,
            sede: sedeFilter || undefined,
            skip: (page - 1) * pageSize,
            limit: pageSize + 1,
          },
          controller.signal
        );
        setHasNext(data.length > pageSize);
        setRecords(data.slice(0, pageSize));
        setError(null);
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    }, 250);

    return () => {
      controller.abort();
      clearTimeout(t);
    };
  }, [jobIdFilter, docFilter, nameFilter, sedeFilter, page, pageSize]);

  function onDownload() {
    if (!records || records.length === 0) return;
    downloadCsv(`records_p${page}.csv`, recordsToCsv(records));
  }

  const rangeStart = records && records.length > 0 ? (page - 1) * pageSize + 1 : 0;
  const rangeEnd = records ? (page - 1) * pageSize + records.length : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Records</h2>
        <button
          onClick={onDownload}
          disabled={!records || records.length === 0}
          className="bg-brand hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded"
        >
          Descargar CSV (página actual)
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-3">
        <FilterInput label="Job ID" value={jobIdFilter} onChange={setJobIdFilter} placeholder="Ej: 1" type="number" />
        <FilterInput label="Documento" value={docFilter} onChange={setDocFilter} placeholder="Ej: 25232067" />
        <FilterInput label="Nombre" value={nameFilter} onChange={setNameFilter} placeholder="Ej: OROZCO" />
        <FilterInput label="Sede" value={sedeFilter} onChange={setSedeFilter} placeholder="Ej: La Mujer" />
      </div>

      {error && <p className="text-sm text-status-error mb-3">{error}</p>}

      {records === null ? (
        <p className="text-sm text-gray-500">Cargando…</p>
      ) : records.length === 0 ? (
        <p className="text-sm text-gray-500">Sin registros para estos filtros.</p>
      ) : (
        <>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <Th>Job</Th>
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
                    <Td>
                      <Link to={`/jobs/${r.job_id}`} className="text-brand hover:underline font-mono">
                        #{r.job_id}
                      </Link>
                    </Td>
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
    </div>
  );
}

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-gray-600 mb-1">{label}</span>
      <input
        type={type}
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
