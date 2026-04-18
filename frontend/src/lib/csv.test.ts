import { describe, expect, it } from "vitest";

import type { RecordRow } from "../api/types";
import { recordsToCsv } from "./csv";

const baseRow: RecordRow = {
  id: 1,
  job_id: 10,
  external_row_id: "A-1",
  patient_document: "111",
  patient_name: "Ana Pérez",
  date_service: "2026-03-02 07:30:00",
  sede: "Bogotá",
  contrato: "Plan Básico",
  captured_at: "2026-04-17T10:00:00Z",
};

describe("recordsToCsv", () => {
  it("writes the expected header row", () => {
    const csv = recordsToCsv([]);
    expect(csv.split("\n")[0]).toBe(
      "id,job_id,no_orden,documento,nombres,fecha_cita,sede,contrato,captured_at"
    );
  });

  it("serializes a row in header order", () => {
    const csv = recordsToCsv([baseRow]);
    const lines = csv.split("\n");
    expect(lines[1]).toBe(
      "1,10,A-1,111,Ana Pérez,2026-03-02 07:30:00,Bogotá,Plan Básico,2026-04-17T10:00:00Z"
    );
  });

  it("quotes and escapes cells with commas, quotes and newlines", () => {
    const row: RecordRow = {
      ...baseRow,
      patient_name: 'Doe, "Jane"',
      sede: "Bogotá\nNorte",
    };
    const line = recordsToCsv([row]).split("\n").slice(1).join("\n");
    expect(line).toContain('"Doe, ""Jane"""');
    expect(line).toContain('"Bogotá\nNorte"');
  });

  it("emits empty string for null/undefined cells", () => {
    const row = { ...baseRow, external_row_id: null, contrato: undefined } as unknown as RecordRow;
    const parts = recordsToCsv([row]).split("\n")[1].split(",");
    expect(parts[2]).toBe("");
    expect(parts[7]).toBe("");
  });

  it("handles multiple rows", () => {
    const csv = recordsToCsv([baseRow, { ...baseRow, id: 2 }]);
    expect(csv.split("\n")).toHaveLength(3);
  });
});
