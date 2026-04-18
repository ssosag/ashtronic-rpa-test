import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

const LIMIT_MIN = 1;
const DATE_MIN = "2000-01-01";
const DATE_MAX = "2100-12-31";

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

function isValidDate(s: string): boolean {
  if (!DATE_RE.test(s)) return false;
  if (s < DATE_MIN || s > DATE_MAX) return false;
  const d = new Date(s);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s;
}

export function NewExtraction() {
  const navigate = useNavigate();
  const [fechaInicial, setFechaInicial] = useState("");
  const [fechaFinal, setFechaFinal] = useState("");
  const [limitInput, setLimitInput] = useState("50");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const limit = Number(limitInput);
  const limitError =
    limitInput.trim() === ""
      ? "El límite es obligatorio."
      : !Number.isInteger(limit)
      ? "El límite debe ser un número entero."
      : limit < LIMIT_MIN
      ? `El límite debe ser mayor o igual a ${LIMIT_MIN}.`
      : null;

  const fechaInicialError =
    fechaInicial === ""
      ? "La fecha inicial es obligatoria."
      : !isValidDate(fechaInicial)
      ? `Fecha inválida. Usa un año entre ${DATE_MIN.slice(0, 4)} y ${DATE_MAX.slice(0, 4)}.`
      : null;

  const fechaFinalError =
    fechaFinal === ""
      ? "La fecha final es obligatoria."
      : !isValidDate(fechaFinal)
      ? `Fecha inválida. Usa un año entre ${DATE_MIN.slice(0, 4)} y ${DATE_MAX.slice(0, 4)}.`
      : null;

  const rangeError =
    !fechaInicialError && !fechaFinalError && fechaInicial > fechaFinal
      ? "La fecha inicial no puede ser posterior a la fecha final."
      : null;

  const hasErrors = !!limitError || !!fechaInicialError || !!fechaFinalError || !!rangeError;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (hasErrors) return;
    setError(null);
    setSubmitting(true);
    try {
      const res = await api.extract({
        fecha_inicial: fechaInicial,
        fecha_final: fechaFinal,
        limit,
      });
      navigate(`/jobs/${res.job_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-xl">
      <h2 className="text-xl font-semibold mb-1">Nueva extracción</h2>
      <p className="text-sm text-gray-600 mb-6">
        El bot se conecta al portal Hiruko, aplica los filtros del convenio y
        extrae las órdenes en el rango indicado.
      </p>

      <form onSubmit={onSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-4 shadow-sm">
        <div>
          <label className="block text-sm font-medium mb-1">Fecha inicial</label>
          <input
            type="date"
            required
            min={DATE_MIN}
            max={DATE_MAX}
            value={fechaInicial}
            onChange={(e) => setFechaInicial(e.target.value)}
            className="w-full rounded border-gray-300 border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
          {fechaInicialError && <p className="text-sm text-status-error mt-1">{fechaInicialError}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Fecha final</label>
          <input
            type="date"
            required
            min={DATE_MIN}
            max={DATE_MAX}
            value={fechaFinal}
            onChange={(e) => setFechaFinal(e.target.value)}
            className="w-full rounded border-gray-300 border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
          {fechaFinalError && <p className="text-sm text-status-error mt-1">{fechaFinalError}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Límite de filas</label>
          <input
            type="number"
            required
            min={LIMIT_MIN}
            step={1}
            value={limitInput}
            onChange={(e) => setLimitInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "-" || e.key === "e" || e.key === "+") e.preventDefault();
            }}
            className="w-full rounded border-gray-300 border px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
          <p className="text-xs text-gray-500 mt-1">
            Mínimo {LIMIT_MIN}. Sin tope superior.
          </p>
          {limitError && <p className="text-sm text-status-error mt-1">{limitError}</p>}
        </div>

        {rangeError && <p className="text-sm text-status-error">{rangeError}</p>}
        {error && <p className="text-sm text-status-error">{error}</p>}

        <button
          type="submit"
          disabled={submitting || hasErrors}
          className="w-full bg-brand hover:bg-brand-hover disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2 rounded transition"
        >
          {submitting ? "Encolando…" : "Ejecutar extracción"}
        </button>
      </form>
    </div>
  );
}
