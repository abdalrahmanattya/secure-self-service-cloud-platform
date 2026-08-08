# ADR-004: Use one application service for every user interface

## Status

Accepted

## Context

The platform exposes a REST API, CLI, and web portal. Reimplementing request
normalization, policy, provider routing, or idempotency in each interface would
allow the same request to produce different outcomes.

## Decision

A provider-neutral application service owns installation setup, request
processing, idempotency, lookup, and simulation orchestration. FastAPI and
Typer are thin adapters over this service. The React portal uses the FastAPI
OpenAPI contract and never reproduces policy logic in TypeScript.

Milestone 5 stores installation and request records in memory for a local,
credential-free demonstration. The API constructs service state through
dependency injection so tests and server instances do not share hidden mutable
global state. Restarting the process intentionally clears demo state.

Environment request creation requires an idempotency key. Reusing a key with
the same request returns the original result; reusing it with different input
is rejected.

No interface exposes an infrastructure apply operation. GitHub proposals and
protected deployment are introduced in Milestone 6.

## Consequences

- API, CLI, and portal users receive the same request identity and policy
  explanation.
- Interface tests can compare outcomes against one shared service.
- Demo state is simple and reproducible but not durable or horizontally
  scalable.
- Persistent storage, authentication, proposal delivery, and deployment remain
  explicit later concerns.
