# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project will use [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

### Notes

- Milestones 3–5 are complete for the credential-free local simulation path.
- Sandbox and enterprise modes describe configuration only. Proposal
  generation, Terraform execution, cloud credentials, apply/destroy workflows,
  and real AWS or Azure resources remain future work.
