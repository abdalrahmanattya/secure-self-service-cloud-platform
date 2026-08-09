import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@mui/material";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { theme } from "../theme";
import { Layout } from "./Layout";

vi.mock("../api/client", () => ({
  api: { installation: vi.fn() },
}));

const configured = {
  provider: "azure" as const,
  installation_id: "demo",
  mode: "enterprise" as const,
  status: "active" as const,
  guardrails: {
    allowed_regions: ["northeurope"],
    budget_maximum: "500.00",
    max_nonproduction_lifetime_days: 30,
    allowed_cluster_sizes: ["small" as const],
  },
};

function renderLayout(
  initialEntries: string[],
  content: ReactNode = <p>Page content</p>,
  seedInstallation = false,
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  if (seedInstallation) {
    queryClient.setQueryData(["installation"], configured);
  }
  return render(
    <ThemeProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route element={<Layout />}>
              <Route path="/" element={content} />
              <Route path="/setup" element={content} />
              <Route path="/readiness" element={content} />
              <Route path="/requests/new" element={content} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.installation).mockResolvedValue(configured);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("Layout", () => {
  it("marks the active navigation item and exposes configured installation context", async () => {
    renderLayout(["/readiness"], <p>Readiness content</p>, true);

    expect(api.installation).toHaveBeenCalled();
    expect(screen.getByRole("link", { name: "Readiness" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(screen.getAllByText("AZURE").length).toBeGreaterThan(0);
    expect(screen.getAllByText("enterprise").length).toBeGreaterThan(0);
    expect(screen.getAllByText("active").length).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/review-only · no direct cloud execution/i).length,
    ).toBeGreaterThan(0);
  });

  it("keeps the shared shell review-only and works at a practical mobile width", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "matchMedia",
      vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    );
    renderLayout(["/requests/new"]);

    expect(screen.getByRole("main")).toBeInTheDocument();
    expect(screen.getByText("Review-only")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /plan|apply|destroy|rollback/i }),
    ).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Open navigation" }));
    expect(
      screen.getAllByRole("navigation", { name: "Primary navigation" }).length,
    ).toBeGreaterThan(0);
  });

  it.each([["/setup"], ["/"]])(
    "suppresses the no-installation alert on %s",
    async (path) => {
      vi.mocked(api.installation).mockRejectedValueOnce(new Error("not found"));
      renderLayout([path]);
      await screen.findByRole("navigation", { name: "Primary navigation" });
      expect(
        screen.queryByText("No installation is configured."),
      ).not.toBeInTheDocument();
    },
  );

  it("keeps the no-installation alert on a request route", async () => {
    vi.mocked(api.installation).mockRejectedValueOnce(new Error("not found"));
    renderLayout(["/requests/new"]);
    expect(
      await screen.findByText("No installation is configured."),
    ).toBeInTheDocument();
  });
});
