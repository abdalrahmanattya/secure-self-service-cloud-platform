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
import { OperationsPage } from "./OperationsPage";
import { ProposalPage } from "./ProposalPage";
import { RequestPage } from "./RequestPage";
import { SetupPage } from "./SetupPage";

vi.mock("../api/client", () => ({
  api: {
    installation: vi.fn(),
    requests: vi.fn(),
    providers: vi.fn(),
    modes: vi.fn(),
    request: vi.fn(),
    proposals: vi.fn(),
    proposal: vi.fn(),
    createRequest: vi.fn(),
    createProposal: vi.fn(),
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

const proposal = {
  schema_version: "proposal.v1",
  proposal_id: "proposal-0123456789abcdef",
  state: "ready_for_review" as const,
  content_hash: "b".repeat(64),
  request_id: "env-0123456789abcdef",
  request_fingerprint: "a".repeat(64),
  installation_id: "demo",
  provider: "azure" as const,
  mode: "simulation" as const,
  artifacts: [
    {
      relative_path: "environments/policies/env-0123456789abcdef.md",
      content: "# Policy summary\n\nDecision: allowed\n",
    },
    {
      relative_path: "environments/proposals/proposal-0123456789abcdef.md",
      content: "# Deployment proposal proposal-0123456789abcdef\n",
    },
    {
      relative_path: "environments/requests/env-0123456789abcdef.json",
      content: '{"application":"payments-api"}\n',
    },
    {
      relative_path: "environments/requests/env-0123456789abcdef.yaml",
      content: "application: payments-api\n",
    },
    {
      relative_path: "environments/terraform/azure/env-0123456789abcdef.json",
      content: '{"provider":"azure"}\n',
    },
  ],
};

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
            <Route path="/operations" element={<OperationsPage />} />
            <Route path="/proposals/:proposalId" element={<ProposalPage />} />
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
  vi.mocked(api.proposals).mockResolvedValue({ proposals: [] });
  vi.mocked(api.proposal).mockResolvedValue(proposal);
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
        description: "Credential-free sandbox proposal generation",
        execution: "proposal-only",
      },
      {
        mode: "enterprise",
        display_name: "Enterprise",
        description: "Credential-free enterprise proposal generation",
        execution: "proposal-only",
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

  it("supports sandbox setup and explains protected proposal execution", async () => {
    const user = userEvent.setup();
    renderPortal(<SetupPage />, ["/setup"]);
    const mode = await screen.findByRole("combobox", { name: "Mode" });
    await user.click(mode);
    await user.click(await screen.findByRole("option", { name: /sandbox/i }));
    expect(mode).toHaveTextContent(/sandbox.*proposal-only/i);
    expect(screen.getByRole("status")).toHaveTextContent(
      /generates deterministic proposals locally without credentials/i,
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      /protected external workflow/i,
    );
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
    [true, /ready for deterministic proposal generation/i],
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

  it("creates a review proposal with a stable attempt key and navigates to its details", async () => {
    const user = userEvent.setup();
    const accepted = record(true);
    vi.mocked(api.request).mockResolvedValue(accepted);
    vi.mocked(api.createProposal).mockResolvedValue(proposal);
    renderPortal(<RequestPage />, ["/requests/env-0123456789abcdef"]);

    await user.click(
      await screen.findByRole("button", { name: /create review proposal/i }),
    );
    expect(api.createProposal).toHaveBeenCalledWith(
      "env-0123456789abcdef",
      expect.any(String),
    );
    expect(
      await screen.findByRole("heading", { name: /deployment proposal/i }),
    ).toBeInTheDocument();
    expect(screen.getByText(proposal.content_hash)).toBeInTheDocument();
  });

  it("does not offer proposal creation for a denied request", async () => {
    vi.mocked(api.request).mockResolvedValue(record(false));
    renderPortal(<RequestPage />, ["/requests/env-0123456789abcdef"]);

    expect(
      await screen.findByText(/denied requests cannot produce/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /create review proposal/i }),
    ).not.toBeInTheDocument();
    expect(api.createProposal).not.toHaveBeenCalled();
  });

  it("shows proposal evidence and a review-only boundary without deployment controls", async () => {
    renderPortal(<ProposalPage />, ["/proposals/proposal-0123456789abcdef"]);

    expect(
      await screen.findByRole("heading", { name: /deployment proposal/i }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(proposal.proposal_id).length).toBeGreaterThan(1);
    expect(screen.getAllByText("Ready for review").length).toBeGreaterThan(0);
    expect(screen.getByText(/review-only boundary/i)).toBeInTheDocument();
    expect(
      screen.getByText(
        "environments/terraform/azure/env-0123456789abcdef.json",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText(
        "environments/requests/env-0123456789abcdef.json content preview",
      ),
    ).toHaveTextContent("payments-api");
    expect(
      screen.queryByRole("button", { name: /plan|apply|destroy|rollback/i }),
    ).not.toBeInTheDocument();
  });

  it("explains an empty, process-memory operations store", async () => {
    renderPortal(<OperationsPage />, ["/operations"]);

    expect(
      await screen.findByRole("heading", { name: "Operations" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/proposal state is held in process memory/i),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(/no proposals are stored in this api process/i),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /plan|apply|destroy/i }),
    ).not.toBeInTheDocument();
  });

  it("lists proposals while marking later lifecycle stages as not executed", async () => {
    vi.mocked(api.proposals).mockResolvedValue({ proposals: [proposal] });
    renderPortal(<OperationsPage />, ["/operations"]);

    expect(
      await screen.findByRole("link", {
        name: /proposal-0123456789abcdef/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Ready for review").length).toBeGreaterThan(1);
    expect(screen.getAllByText("Not executed").length).toBeGreaterThan(1);
    expect(
      screen.queryByRole("button", { name: /plan|apply|destroy/i }),
    ).not.toBeInTheDocument();
  });
});
