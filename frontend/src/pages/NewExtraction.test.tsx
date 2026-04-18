import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { NewExtraction } from "./NewExtraction";

const extractMock = vi.fn();
const navigateMock = vi.fn();

vi.mock("../api/client", () => ({
  api: {
    extract: (...args: unknown[]) => extractMock(...args),
  },
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return { ...actual, useNavigate: () => navigateMock };
});

function renderPage() {
  return render(
    <MemoryRouter>
      <NewExtraction />
    </MemoryRouter>
  );
}

function setDate(input: HTMLElement, value: string) {
  // <input type="date"> doesn't play well with userEvent.type in jsdom.
  fireEvent.change(input, { target: { value } });
}

beforeEach(() => {
  extractMock.mockReset();
  navigateMock.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("NewExtraction", () => {
  it("keeps submit disabled while the form is empty", () => {
    renderPage();
    const btn = screen.getByRole("button", { name: /ejecutar extracción/i });
    expect(btn).toBeDisabled();
  });

  it("shows an error when limit is zero", async () => {
    const user = userEvent.setup();
    renderPage();
    const limitInput = screen.getByLabelText(/límite de filas/i);
    await user.clear(limitInput);
    await user.type(limitInput, "0");
    expect(screen.getByText(/debe ser mayor o igual a 1/i)).toBeInTheDocument();
  });

  it("rejects a reversed date range", () => {
    renderPage();
    setDate(screen.getByLabelText(/fecha inicial/i), "2026-02-01");
    setDate(screen.getByLabelText(/fecha final/i), "2026-01-01");
    expect(screen.getByText(/no puede ser posterior/i)).toBeInTheDocument();
  });

  it("submits and navigates on success", async () => {
    extractMock.mockResolvedValueOnce({ job_id: 42, status: "queued", message: "ok" });
    const user = userEvent.setup();
    renderPage();
    setDate(screen.getByLabelText(/fecha inicial/i), "2026-01-01");
    setDate(screen.getByLabelText(/fecha final/i), "2026-01-31");
    await user.click(screen.getByRole("button", { name: /ejecutar extracción/i }));

    expect(extractMock).toHaveBeenCalledWith({
      fecha_inicial: "2026-01-01",
      fecha_final: "2026-01-31",
      limit: 50,
    });
    expect(navigateMock).toHaveBeenCalledWith("/jobs/42");
  });
});
