import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { RecordRow } from "../api/types";
import { downloadCsv, recordsToCsv } from "../lib/csv";

export function RecordsList() {
  const [records, setRecords] = useState<RecordRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [jobIdFilter, setJobIdFilter] = useState("");
  const [docFilter, setDocFilter] = useState("");
  const [nameFilter, setNameFilter] = useState("");
  const [sedeFilter, setSedeFilter] = useState("");

  useEffect(() => {
    let cancelled = false;
    const t = setTimeout(async () => {
      try {
        const data = await api.listRecords({
          job_id: jobIdFilter ? Number(jobIdFilter) : undefined,
          patient_document: docFilter || undefined,
          patient_name: nameFilter || undefined,
          sede: sedeFilter || undefined,
          limit: 500,
        });
        if (!cancelled) {
          setRecords(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      }
    }, 250); // debounce

    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [jobIdFilter, docFilter, nameFilter, sedeFilter]);

  function onDownload() {
    if (!records || records.length === 0) return;
    downloadCsv("records.csv", recordsToCsv(records));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Records</h2>
        <button
          onClick={onDownload}
          disabled={!records || records.length === 0}
          className="bg-brand hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded"
        >
          Descargar CSV
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
          <p className="text-xs text-gray-500 mb-2">{records.length} registros</p>
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
