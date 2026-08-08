# Shared interfaces

The API, CLI, and portal are three views over one `PlatformService`. The
service owns exactly one provider-locked `InstallationProfile` and a
process-local request/idempotency store. Interfaces do not implement separate
policy rules: they construct the immutable domain request and call the same
service operation.

## Equivalence

For a given installation and normalized request, all interfaces expose the
same `request_id`, fingerprint, policy decision, violations, and simulated
resources. Provider is resolved from the installation profile. It is never an
input on `EnvironmentRequest` and is not editable on the portal request form.

The API and CLI use stable JSON field names and sorted deterministic values.
The portal uses the API response directly and presents policy violations next
to the field named by each violation.

## HTTP endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/v1/platform/installations` | Create and activate the one validated installation profile. |
| `GET` | `/v1/platform/installation` | Read the current profile. |
| `POST` | `/v1/platform/installation/validate` | Validate provider-specific readiness. |
| `GET` | `/v1/platform/providers` | Discover AWS and Azure simulation providers. |
| `GET` | `/v1/platform/modes` | Discover simulation, sandbox, and enterprise descriptions. |
| `POST` | `/v1/environment-requests` | Validate, store, and simulate a request. |
| `GET` | `/v1/environment-requests` | List deterministic request records. |
| `GET` | `/v1/environment-requests/{request_id}` | Read one request record. |
| `GET` | `/health` | Local process health. |
| `GET` | `/version` | Application name and version. |
| `GET` | `/metrics` | Deterministic local text metrics. |

There are intentionally no deployment proposal, apply, destroy, Terraform,
cloud credential, or provider SDK endpoints in this milestone.

Syntactically valid requests are processed into an `EnvironmentRequestRecord`
even when common or provider policy denies them. The API returns that record
with HTTP `200`, including its stable request ID and friendly violations, so a
caller can inspect and correct the request. HTTP `422` is reserved for
malformed transport/domain input and rejected installation configuration.

## CLI commands

```text
platform setup init --provider aws|azure --mode simulation|sandbox|enterprise \
  [--output PROFILE.json] [--force]
platform setup validate PROFILE.json|PROFILE.yaml
platform setup status PROFILE.json|PROFILE.yaml
platform request validate REQUEST.json|REQUEST.yaml --profile PROFILE.json|PROFILE.yaml
platform request render REQUEST.json|REQUEST.yaml --profile PROFILE.json|PROFILE.yaml
```

`setup init` prints stable JSON and writes a profile only when the explicit
`--output` path is supplied. Existing files are protected unless `--force` is
provided. Validation and status reconstruct the profile from that file.

Request validation and rendering also reconstruct an isolated service from
the required active profile file. They therefore work across separate CLI
processes and produce the same IDs and decisions as direct service/API calls.
There is no CLI apply or propose command. Request status is intentionally not
part of this public process-independent command set; the request store remains
an in-memory API/service demo boundary.

All commands print stable JSON. Validation and policy failures print a typed
error or decision and return a nonzero exit status. `render` describes the
resources that would be created by the simulation; it never applies
infrastructure.

## Portal pages

- **Setup** selects the provider and installation mode once. Sandbox and
  enterprise are visibly configuration-only in this demo.
- **Dashboard** summarizes the installation and request history.
- **New environment** collects business and platform requirements without
  requiring Terraform knowledge. The provider is displayed from the profile,
  and the profile's first allowed region is prefilled.
- **Request result** displays accepted or denied records, field-level policy
  feedback, stable request ID, and simulated resources.
- **Readiness** explains the selected provider, mode, and simulation boundary.

The portal uses React Router, TanStack Query, React Hook Form, Material UI,
and a client typed from OpenAPI. `web/openapi.json` is exported locally by
`scripts/export-openapi.py`; `npm run generate:api` (from the `web`
directory) regenerates `src/api/generated.ts` with the exact-pinned
`openapi-typescript` tool. The generated file is not hand-maintained.

## Idempotency

`POST /v1/environment-requests` requires a non-empty `Idempotency-Key` header.
The service compares that key with the normalized request fingerprint under an
in-process lock:

- the same key and same normalized payload returns the original record;
- the same key and a different normalized payload returns HTTP `409`;
- a different key for the same deterministic request binds to the existing
  canonical record without changing its stored metadata;
- blank or missing keys return a typed HTTP `400` error.

The portal creates one key per submission attempt and reuses it for retries.
A new form submission after navigation creates a new attempt key.

## State and safety boundary

State is explicitly demo-only and exists in memory for the lifetime of one
service instance. Restarting the API loses the installation and request list.
The service does not read environment variables, files, credentials, cloud
configuration, or telemetry destinations. Both provider adapters are
credential-free simulation adapters. AWS and Azure setup defaults select
`eu-west-1` and `northeurope` respectively; an unsupported region is rejected
before the profile is stored, so setup can be retried.

Sandbox and enterprise modes describe future readiness, but this milestone
rejects request execution outside simulation mode. No interface can run
`terraform apply` or make a cloud call.
