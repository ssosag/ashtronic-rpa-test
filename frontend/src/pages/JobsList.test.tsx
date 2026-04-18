import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { Job } from "../api/types";
import { JobsList } from "./JobsList";

const listJobsMock = vi.fn();

vi.mock("../api/client", () => ({
  api: {
    listJobs: (...args: unknown[]) => listJobsMock(...args),
  },
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <JobsList />
    </MemoryRouter>
  );
}

beforeEach(() => {
  listJobsMock.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("JobsList", () => {
  it("renders empty state when the API returns no jobs", async () => {
    listJobsMock.mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText(/no hay trabajos todavía/i)).toBeInTheDocument();
  });

  it("renders a row per job", async () => {
    const jobs: Job[] = [
      {
        id: 1,
        status: "done",
        fecha_inicial: "2026-01-01",
        fecha_final: "2026-01-31",
        limit: 10,
        started_at: "2026-01-01T10:00:00Z",
        finished_at: "2026-01-01T10:01:00Z",
        records_count: 7,
        retries_count: 0,
        error_message: null,
        created_at: "2026-01-01T10:00:00Z",
      },
      {
        id: 2,
        status: "error",
        fecha_inicial: "2026-02-01",
        fecha_final: "2026-02-28",
        limit: 5,
        started_at: null,
        finished_at: null,
        records_count: 0,
        retries_count: 2,
        error_message: "portal rejected credentials",
        created_at: "2026-02-01T10:00:00Z",
      },
    ];
    listJobsMock.mockResolvedValue(jobs);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Completado")).toBeInTheDocument();
      expect(screen.getByText("Error")).toBeInTheDocument();
    });
    expect(screen.getByText("2026-01-01 → 2026-01-31")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /ver/i })).toHaveLength(2);
  });

  it("displays an error message when the API fails", async () => {
    listJobsMock.mockRejectedValueOnce(new Error("network down"));
    renderPage();
    expect(await screen.findByText(/network down/i)).toBeInTheDocument();
  });
});
