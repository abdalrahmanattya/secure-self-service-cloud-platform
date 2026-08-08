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

type ProvidersResponse =
  paths["/v1/platform/providers"]["get"]["responses"][200]["content"]["application/json"];
type ModesResponse =
  paths["/v1/platform/modes"]["get"]["responses"][200]["content"]["application/json"];
type RequestsResponse =
  paths["/v1/environment-requests"]["get"]["responses"][200]["content"]["application/json"];

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
  createRequest: (
    input: EnvironmentRequestInput,
    idempotencyKey: string,
  ): Promise<EnvironmentRequestRecord> =>
    request("/v1/environment-requests", {
      method: "POST",
      headers: { "Idempotency-Key": idempotencyKey },
      body: JSON.stringify(input),
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
