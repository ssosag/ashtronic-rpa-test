import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders the Spanish label for each status", () => {
    const cases: [Parameters<typeof StatusBadge>[0]["status"], string][] = [
      ["queued", "En cola"],
      ["running", "En curso"],
      ["done", "Completado"],
      ["error", "Error"],
    ];
    for (const [status, label] of cases) {
      const { unmount } = render(<StatusBadge status={status} />);
      expect(screen.getByText(label)).toBeInTheDocument();
      unmount();
    }
  });
});
