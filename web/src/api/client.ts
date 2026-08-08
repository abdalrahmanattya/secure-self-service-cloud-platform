import type { components, paths } from "./generated";

export type Provider = components["schemas"]["CloudProvider"];
export type InstallationMode = components["schemas"]["InstallationMode"];
export type EnvironmentRequestInput =
  components["schemas"]["EnvironmentRequest"];
export type InstallationProfile = components["schemas"]["InstallationProfile"];
export type InstallationResponse =
  components["schemas"]["InstallationResponse"];
export type EnvironmentRequestRecord =
  components["schemas"]["EnvironmentRequestRecord"];
export type ProviderDescriptor = components["schemas"]["ProviderDescriptor"];
export type ModeDescriptor = components["schemas"]["ModeDescriptor"];
export type PolicyViolation = components["schemas"]["PolicyViolation"];
export type DeploymentProposal = components["schemas"]["DeploymentProposal"];
export type ProposalArtifact = components["schemas"]["ProposalArtifact"];

export type ApiErrorField = {
  code: string;
  field: string;
  message: string;
};

export type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    fields?: ApiErrorField[];
  };
};

type ProvidersResponse =
  paths["/v1/platform/providers"]["get"]["responses"][200]["content"]["application/json"];
type ModesResponse =
  paths["/v1/platform/modes"]["get"]["responses"][200]["content"]["application/json"];
type RequestsResponse =
  paths["/v1/environment-requests"]["get"]["responses"][200]["content"]["application/json"];
type ProposalsResponse =
  paths["/v1/deployment-proposals"]["get"]["responses"][200]["content"]["application/json"];

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = (await response.json()) as T | { error?: unknown };
  if (!response.ok) {
    if (
      response.status === 422 &&
      typeof body === "object" &&
      body !== null &&
      "outcome" in body
    ) {
      return body as T;
    }
    throw body;
  }
  return body as T;
}

export const api = {
  installation: (): Promise<InstallationProfile> =>
    request("/v1/platform/installation"),
  providers: (): Promise<ProvidersResponse> =>
    request("/v1/platform/providers"),
  modes: (): Promise<ModesResponse> => request("/v1/platform/modes"),
  requests: (): Promise<RequestsResponse> =>
    request("/v1/environment-requests"),
  request: (id: string): Promise<EnvironmentRequestRecord> =>
    request(`/v1/environment-requests/${encodeURIComponent(id)}`),
  proposals: (): Promise<ProposalsResponse> =>
    request("/v1/deployment-proposals"),
  proposal: (id: string): Promise<DeploymentProposal> =>
    request(`/v1/deployment-proposals/${encodeURIComponent(id)}`),
  createRequest: (
    input: EnvironmentRequestInput,
    idempotencyKey: string,
  ): Promise<EnvironmentRequestRecord> =>
    request("/v1/environment-requests", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(input),
    }),
  createProposal: (
    requestId: string,
    idempotencyKey: string,
  ): Promise<DeploymentProposal> =>
    request("/v1/deployment-proposals", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ request_id: requestId }),
    }),
  createInstallation: (
    provider: Provider,
    mode: InstallationMode,
  ): Promise<InstallationResponse> =>
    request("/v1/platform/installations", {
      method: "POST",
      body: JSON.stringify({ provider, mode }),
    }),
};

export function apiErrorMessage(
  error: unknown,
  fallback = "The API could not complete the operation.",
): string {
  if (typeof error === "object" && error !== null && "error" in error) {
    const payload = error as ApiErrorPayload;
    if (payload.error?.message) return payload.error.message;
  }
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}

export function apiErrorFields(error: unknown): ApiErrorField[] {
  if (typeof error === "object" && error !== null && "error" in error) {
    const payload = error as ApiErrorPayload;
    return payload.error?.fields ?? [];
  }
  return [];
}
