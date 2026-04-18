import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { RecordDetail as RecordDetailType } from "../api/types";
import { RecordDetail } from "./RecordDetail";

const getRecordMock = vi.fn();

vi.mock("../api/client", () => ({
  api: {
    getRecord: (...args: unknown[]) => getRecordMock(...args),
  },
}));

function renderAt(id: string) {
  return render(
    <MemoryRouter initialEntries={[`/records/${id}`]}>
      <Routes>
        <Route path="/records/:id" element={<RecordDetail />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  getRecordMock.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("RecordDetail", () => {
  it("renders normalized fields and the raw_row_json block", async () => {
    const record: RecordDetailType = {
      id: 5,
      job_id: 10,
      external_row_id: "ORD-1",
      patient_name: "Ana Pérez",
      patient_document: "111",
      date_service: "2026-03-02 07:30:00",
      sede: "Bogotá",
      contrato: "Plan Básico",
      captured_at: "2026-04-17T10:00:00Z",
      raw_row_json: { "No. Orden": "ORD-1", Documento: "111" },
    };
    getRecordMock.mockResolvedValueOnce(record);

    renderAt("5");

    expect(await screen.findByText("Ana Pérez")).toBeInTheDocument();
    expect(screen.getByText("111")).toBeInTheDocument();
    expect(screen.getByText("Bogotá")).toBeInTheDocument();

    // raw_row_json rendered as pretty-printed JSON inside a <pre>
    const pre = screen.getByText(/"No\. Orden": "ORD-1"/);
    expect(pre.tagName).toBe("PRE");
  });

  it("shows the error message when the API fails", async () => {
    getRecordMock.mockRejectedValueOnce(new Error("not found"));
    renderAt("999");
    expect(await screen.findByText(/not found/i)).toBeInTheDocument();
  });
});
