# Shared interfaces

The API, CLI, and portal are three views over one `PlatformService`. The
service owns exactly one provider-locked `InstallationProfile` and a
process-local request, proposal, and idempotency stores. Interfaces do not
implement separate policy rules: they construct the immutable domain request
and call the same service operations.

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
| `POST` | `/v1/deployment-proposals` | Idempotently create a deterministic proposal for an accepted request. |
| `GET` | `/v1/deployment-proposals` | List proposals in stable proposal-ID order. |
| `GET` | `/v1/deployment-proposals/{proposal_id}` | Read one immutable proposal. |
| `GET` | `/health` | Local process health. |
| `GET` | `/version` | Application name and version. |
| `GET` | `/metrics` | Deterministic local text metrics. |

There is intentionally no API plan, apply, rollback, drift, or destroy endpoint.
Proposal creation is local and credential-free; it does not create a pull
request or call Terraform/provider APIs.

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
platform request propose REQUEST.json|REQUEST.yaml --profile PROFILE.json|PROFILE.yaml \
  [--output BUNDLE] [--force]
platform request status REQUEST_OR_PROPOSAL_ID_OR_FILE [--profile PROFILE]
```

`setup init` prints stable JSON and writes a profile only when the explicit
`--output` path is supplied. Existing files are protected unless `--force` is
provided. Validation and status reconstruct the profile from that file.

Request validation and rendering also reconstruct an isolated service from
the required active profile file. They therefore work across separate CLI
processes and produce the same IDs and decisions as direct service/API calls.
`request propose` emits the full proposal as stable JSON and optionally
materializes its seven artifacts plus the safety marker. `request status` reads
a full saved proposal JSON document, evaluates a standalone request document
when `--profile` is supplied, or resolves a process-local ID when invoked in the
same service process. IDs are not durable across separate CLI/API processes.

All commands print stable JSON. Validation and policy failures print a typed
error or decision and return a nonzero exit status. `render` describes the
resources that would be created by the simulation; it never applies
infrastructure.

## Portal pages

- **Setup** selects the provider and installation mode once, then locks the
  provider for the installation. All modes can
  evaluate requests and create local review proposals; simulation also
  returns mocked provider resources, while sandbox and enterprise remain
  proposal-only until protected deployment is configured.
- **Dashboard** summarizes installation context with API-derived request,
  accepted-request, proposal, and zero-cloud-change metrics.
- **New environment** groups business and platform requirements without
  requiring Terraform knowledge. The provider is displayed from the profile,
  and the profile's first allowed region is prefilled; a live summary follows
  application, environment, region, budget, and installation context.
- **Request review** displays accepted or denied records, field-level policy
  feedback, stable request ID, simulated resources, and **Create review
  proposal** only for accepted requests.
- **Proposal evidence** shows **Ready for review**, provider/mode, request link,
  content hash, schema, expandable artifact previews, and accessible copy
  feedback.
- **Operations** lists process-memory proposals and marks GitHub review and all
  later protected stages **Guarded** and not executed.
- **Readiness** explains the selected provider, mode, available capabilities,
  guarded prerequisites, and zero direct cloud changes.

The shell uses a responsive dark sidebar on desktop and an **Open navigation**
mobile drawer on smaller screens. There are no portal controls for plan, apply,
drift, rollback, or destroy.

The portal uses React Router, TanStack Query, React Hook Form, Material UI,
and a client typed from OpenAPI. `web/openapi.json` is exported locally by
`scripts/export-openapi.py`; `npm run generate:api` (from the `web`
directory) regenerates `src/api/generated.ts` with the exact-pinned
`openapi-typescript` tool. The generated file is not hand-maintained.

## Idempotency

`POST /v1/environment-requests` and `POST /v1/deployment-proposals` require a
non-empty `Idempotency-Key` header.
The service compares that key with the normalized request fingerprint under an
in-process lock:

- the same key and same normalized payload returns the original record;
- the same key and a different normalized payload returns HTTP `409`;
- a different key for the same deterministic request binds to the existing
  canonical record without changing its stored metadata;
- blank or missing keys return a typed HTTP `400` error.

The portal creates one key per submission attempt and reuses it for retries.
A new form submission after navigation creates a new attempt key.

Proposal retries with the same key/request return the same proposal and HTTP
`201`; key reuse for another request returns `409`. Different keys for the same
deterministic request converge on its canonical proposal ID/content.

## State and safety boundary

State is explicitly demo-only and exists in memory for the lifetime of one
service instance. Restarting the API loses the installation, request list,
proposal list, and idempotency bindings.
The service does not read environment variables, files, credentials, cloud
configuration, or telemetry destinations. Both provider adapters are
credential-free simulation adapters. AWS and Azure setup defaults select
`eu-west-1` and `northeurope` respectively; an unsupported region is rejected
before the profile is stored, so setup can be retried.

All modes support credential-free request evaluation and deterministic proposal
generation. Simulation can additionally return mocked provider resources.
Sandbox and enterprise are proposal-only locally: no interface can run
`terraform apply` or make a cloud call. Cloud lifecycle operations are limited
to separately configured, protected GitHub workflows, which are disabled and
unexecuted in this release.
