import type { ReactNode } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@mui/material";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";
import { theme } from "../theme";
import { DashboardPage } from "./DashboardPage";
import { NewRequestPage } from "./NewRequestPage";
import { RequestPage } from "./RequestPage";
import { SetupPage } from "./SetupPage";

vi.mock("../api/client", () => ({
  api: {
    installation: vi.fn(),
    requests: vi.fn(),
    providers: vi.fn(),
    modes: vi.fn(),
    request: vi.fn(),
    createRequest: vi.fn(),
    createInstallation: vi.fn(),
  },
}));

const installation = {
  provider: "azure" as const,
  installation_id: "demo",
  mode: "simulation" as const,
  status: "active" as const,
  guardrails: {
    allowed_regions: ["northeurope"],
    budget_maximum: "500.00",
    max_nonproduction_lifetime_days: 30,
    allowed_cluster_sizes: ["small" as const],
  },
};

const record = (allowed: boolean) => ({
  request: {
    application: "payments-api",
    environment: "development" as const,
    owner: "Platform Team",
    cost_centre: "FIN-042",
    data_classification: "internal" as const,
    region: "northeurope",
    network_cidr: allowed ? "10.42.0.0/16" : "8.8.8.0/24",
    cluster_size: "small" as const,
    monthly_budget: "250.00",
    business_justification: "development environment",
    non_production_expiry: "2026-08-20",
    provider: "azure" as const,
    canonical_json: "{}",
    fingerprint: "a".repeat(64),
    request_id: "env-0123456789abcdef",
  },
  outcome: {
    decision: {
      allowed,
      violations: allowed
        ? []
        : [
            {
              code: "network-must-be-private-ipv4",
              message: "The network must use a private IPv4 CIDR.",
              field: "network_cidr",
            },
          ],
    },
    result: null,
  },
  state: allowed ? ("accepted" as const) : ("denied" as const),
  idempotency_key: "stable-test-key",
});

function renderPortal(element: ReactNode, initialEntries = ["/"]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <ThemeProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/" element={element} />
            <Route path="/setup" element={<SetupPage />} />
            <Route path="/requests/new" element={<NewRequestPage />} />
            <Route path="/requests/:requestId" element={<RequestPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </ThemeProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.installation).mockResolvedValue(installation);
  vi.mocked(api.requests).mockResolvedValue({ requests: [] });
  vi.mocked(api.providers).mockResolvedValue({
    providers: [
      {
        provider: "aws",
        display_name: "Amazon Web Services",
        description: "AWS simulation",
        available: true,
      },
      {
        provider: "azure",
        display_name: "Microsoft Azure",
        description: "Azure simulation",
        available: true,
      },
    ],
  });
  vi.mocked(api.modes).mockResolvedValue({
    modes: [
      {
        mode: "simulation",
        display_name: "Simulation",
        description: "Local simulation",
        execution: "simulation-only",
      },
      {
        mode: "sandbox",
        display_name: "Sandbox",
        description: "Future sandbox",
        execution: "not-enabled-in-demo",
      },
      {
        mode: "enterprise",
        display_name: "Enterprise",
        description: "Future enterprise",
        execution: "not-enabled-in-demo",
      },
    ],
  });
});

afterEach(() => cleanup());

describe("portal interfaces", () => {
  it("renders accessible dashboard headings when setup is missing", async () => {
    vi.mocked(api.installation).mockRejectedValueOnce(new Error("not found"));
    renderPortal(<DashboardPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      /set up an installation/i,
    );
  });

  it("supports setup selection and explains non-executable modes", async () => {
    const user = userEvent.setup();
    renderPortal(<SetupPage />, ["/setup"]);
    const mode = await screen.findByRole("combobox", { name: "Mode" });
    await user.click(mode);
    await user.click(await screen.findByRole("option", { name: /sandbox/i }));
    expect(screen.getByRole("status")).toHaveTextContent(/configuration-only/i);
    await user.click(
      screen.getByRole("button", { name: /create installation/i }),
    );
    expect(api.createInstallation).toHaveBeenCalledWith("aws", "sandbox");
  });

  it("keeps setup defaults in range while discovery is loading", () => {
    vi.mocked(api.providers).mockReturnValueOnce(new Promise<never>(() => {}));
    vi.mocked(api.modes).mockReturnValueOnce(new Promise<never>(() => {}));

    renderPortal(<SetupPage />, ["/setup"]);

    expect(
      screen.getByRole("combobox", { name: "Provider" }),
    ).toHaveTextContent("Loading providers…");
    expect(screen.getByRole("combobox", { name: "Mode" })).toHaveTextContent(
      "Loading modes…",
    );
  });

  it("prefills the configured region and never exposes provider as a field", async () => {
    renderPortal(<NewRequestPage />, ["/requests/new"]);
    expect(await screen.findByDisplayValue("northeurope")).toBeInTheDocument();
    expect(
      screen.queryByRole("combobox", { name: "Provider" }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /new environment/i }),
    ).toBeInTheDocument();
  });

  it.each([
    [true, /ready as a deterministic simulation/i],
    [false, /the network must use a private ipv4 cidr/i],
  ])(
    "navigates to a %s request result with policy feedback",
    async (allowed, message) => {
      const user = userEvent.setup();
      const result = record(allowed);
      vi.mocked(api.createRequest).mockResolvedValue(result);
      vi.mocked(api.request).mockResolvedValue(result);
      renderPortal(<NewRequestPage />, ["/requests/new"]);
      await user.type(
        await screen.findByLabelText("Application"),
        "payments-api",
      );
      await user.type(screen.getByLabelText("Owner"), "Platform Team");
      await user.type(screen.getByLabelText("Cost centre"), "FIN-042");
      await user.type(
        screen.getByLabelText(/why is this environment/i),
        "development environment",
      );
      await user.click(screen.getByRole("button", { name: /review request/i }));
      expect(
        await screen.findByRole("heading", { name: /payments-api/i }),
      ).toBeInTheDocument();
      const alerts = await screen.findAllByRole("alert");
      expect(
        alerts.some((alert) => message.test(alert.textContent ?? "")),
      ).toBe(true);
      const [submitted, key] = vi.mocked(api.createRequest).mock.calls[0];
      expect(submitted).toEqual(
        expect.objectContaining({ region: "northeurope" }),
      );
      expect(submitted).not.toHaveProperty("provider");
      expect(key).toEqual(expect.any(String));
    },
  );
});
