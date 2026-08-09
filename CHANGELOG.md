# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project will use [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026-08-09

The first stable portfolio release provides a credential-free AWS/Azure
self-service platform demonstration, deterministic proposal evidence, and
reviewed real-deployment designs. No real cloud setup, authentication,
approval, or operation was run for this release.

### Added

- Initial portfolio, governance, and architecture foundation.
- Provider-neutral immutable installation, request, policy, adapter, and
  simulation contracts.
- Deterministic request normalization with canonical JSON, SHA-256 fingerprint,
  and stable request ID.
- Credential-free fake-adapter coverage for AWS and Azure simulation routes.
- Deterministic AWS and Azure provider simulation adapters with provider-native
  networking, Kubernetes, identity, encryption, observability, security, and
  budget controls.
- A shared `PlatformService` consumed by the FastAPI API, Typer CLI, and React
  portal, with stable policy feedback and idempotent in-memory request records.
- A public simulation quickstart covering Python, API, CLI, and web startup.
- Deterministic deployment proposal models, in-memory idempotent persistence,
  FastAPI create/list/detail endpoints, CLI bundle materialization/status, and
  portal proposal/operations views.
- Provider-specific AWS and Azure Terraform roots and modules, separate
  operator-run bootstrap roots, remote-state configuration contracts, and
  environment-bound OIDC identities for plan, apply, and destroy.
- Common, AWS, and Azure OPA policies validated with pinned Conftest fixtures.
- Manual protected plan, apply, drift, rollback, destroy-plan, and destroy-apply
  workflow definitions with exact bindings, independent-review checks,
  concurrency, protected Environments, and short-lived OIDC.
- Non-root multi-stage API and portal container definitions and a hardened Helm
  chart for the two workloads.
- Portfolio-grade documentation covering deterministic proposal
  bundles, GitHub-only protected deployment, AWS and Azure sandbox/enterprise
  designs, Terraform and policy references, OIDC, state, security, cost,
  operations, drift, rollback, destroy, incidents, troubleshooting, and the
  v1.0.0 release record.
- Mermaid source and rendered SVGs for the component, lifecycle, provider,
  state, policy, logging, trust-boundary, and incident views.

### Notes

- Milestones 1–7 are implemented and validated within the credential-free
  portfolio-release boundary.
- Proposal persistence is process-local and the truthful proposal state is
  `ready_for_review`; protected GitHub approval is external to that state.
- Simulation, sandbox, and enterprise installations all support credential-free
  request evaluation and deterministic proposal generation. Sandbox and
  enterprise proposals remain local review bundles until protected deployment
  is separately configured.
- `REAL_DEPLOYMENT_ENABLED` remains absent or false. Operators must separately
  configure protected GitHub Environments, required reviewers, deployment
  branches, repository variables, provider identifiers, and bootstrap output.
- A private repository is required by the included real-capable jobs. Proposal
  and saved-plan artifacts are retained for one day; saved plans can contain
  sensitive values and must be handled as protected data.
- The MkDocs documentation is published through an HTTPS GitHub Pages site.
- No live AWS or Azure validation, bootstrap, plan, apply, rollback, drift,
  destroy, or cloud resource operation is claimed.

[Unreleased]: https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/releases/tag/v1.0.0
