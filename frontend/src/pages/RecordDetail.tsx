import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { RecordDetail as RecordDetailType } from "../api/types";

export function RecordDetail() {
  const { id } = useParams<{ id: string }>();
  const [record, setRecord] = useState<RecordDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const controller = new AbortController();
    (async () => {
      try {
        const data = await api.getRecord(Number(id), controller.signal);
        setRecord(data);
        setError(null);
      } catch (e) {
        if (controller.signal.aborted) return;
        setError(e instanceof Error ? e.message : String(e));
      }
    })();
    return () => controller.abort();
  }, [id]);

  if (error) {
    return (
      <div>
        <BackLink />
        <p className="text-sm text-status-error mt-4">{error}</p>
      </div>
    );
  }

  if (!record) {
    return (
      <div>
        <BackLink />
        <p className="text-sm text-gray-500 mt-4">Cargando…</p>
      </div>
    );
  }

  return (
    <div>
      <BackLink />

      <h2 className="text-xl font-semibold mt-4 mb-4">
        Registro #{record.id}{" "}
        <Link to={`/jobs/${record.job_id}`} className="text-brand hover:underline text-base">
          (job #{record.job_id})
        </Link>
      </h2>

      <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm mb-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Campos normalizados</h3>
        <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-3 text-sm">
          <Field label="No. orden" value={record.external_row_id} mono />
          <Field label="Documento" value={record.patient_document} />
          <Field label="Nombre" value={record.patient_name} />
          <Field label="Fecha cita" value={record.date_service} />
          <Field label="Sede" value={record.sede} />
          <Field label="Contrato" value={record.contrato} />
          <Field label="Capturado" value={new Date(record.captured_at).toLocaleString()} />
        </dl>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Fila completa del portal (<code className="text-xs">raw_row_json</code>)
        </h3>
        <pre className="bg-gray-50 border border-gray-200 rounded p-3 text-xs overflow-x-auto font-mono">
          {JSON.stringify(record.raw_row_json, null, 2)}
        </pre>
      </div>
    </div>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string | null; mono?: boolean }) {
  return (
    <div>
      <dt className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</dt>
      <dd className={`mt-0.5 text-gray-900 ${mono ? "font-mono" : ""}`}>
        {value ?? <span className="text-gray-400">—</span>}
      </dd>
    </div>
  );
}

function BackLink() {
  return (
    <Link to="/records" className="text-sm text-brand hover:underline">
      ← Volver a Records
    </Link>
  );
}
