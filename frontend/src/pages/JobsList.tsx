import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";

const REFRESH_MS = 2000;

export function JobsList() {
  const [jobs, setJobs] = useState<Job[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const tick = async () => {
      try {
        const data = await api.listJobs();
        if (cancelled) return;
        setJobs(data);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
      }
      timer = setTimeout(tick, REFRESH_MS);
    };

    tick();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Jobs</h2>
      </div>

      {error && <p className="text-sm text-status-error mb-3">{error}</p>}

      {jobs === null ? (
        <p className="text-sm text-gray-500">Cargando…</p>
      ) : jobs.length === 0 ? (
        <p className="text-sm text-gray-500">No hay trabajos todavía.</p>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <Th>ID</Th>
                <Th>Estado</Th>
                <Th>Rango</Th>
                <Th className="text-right">Límite</Th>
                <Th className="text-right">Registros</Th>
                <Th>Creado</Th>
                <Th>Finalizado</Th>
                <Th></Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {jobs.map((j) => (
                <tr key={j.id} className="hover:bg-gray-50">
                  <Td className="font-mono">{j.id}</Td>
                  <Td><StatusBadge status={j.status} /></Td>
                  <Td>{j.fecha_inicial} → {j.fecha_final}</Td>
                  <Td className="text-right">{j.limit}</Td>
                  <Td className="text-right">{j.records_count}</Td>
                  <Td>{fmt(j.created_at)}</Td>
                  <Td>{j.finished_at ? fmt(j.finished_at) : "—"}</Td>
                  <Td>
                    <Link
                      to={`/jobs/${j.id}`}
                      className="text-brand hover:underline"
                    >
                      Ver
                    </Link>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function Th({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return (
    <th className={`px-4 py-2 text-left font-medium ${className}`}>{children}</th>
  );
}

function Td({ children, className = "" }: { children?: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-2 ${className}`}>{children}</td>;
}

function fmt(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString();
}
