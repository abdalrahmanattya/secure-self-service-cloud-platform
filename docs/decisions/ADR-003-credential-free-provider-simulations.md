# ADR-003: Model provider designs without contacting cloud APIs

## Status

Accepted

## Context

The common domain defines AWS and Azure adapter ports, but the product must
demonstrate meaningful provider differences before any account, subscription,
credential, state backend, or billable resource is introduced.

## Decision

Milestones 3 and 4 implement deterministic simulation adapters. Each adapter
validates provider-specific regions and returns provider-native resource
descriptions containing the security, identity, networking, Kubernetes,
logging, and budget controls that the provider Terraform implementations must
provide.

The adapters do not import cloud SDKs, read environment credentials, call
external services, create remote identifiers, or execute Terraform. AWS and
Azure stay in separate modules and only the adapter selected by the immutable
installation profile is invoked.

Simulation descriptions are contracts and review evidence, not claims that
infrastructure exists.

## Consequences

- Both cloud designs can be reviewed and tested without cloud access or cost.
- Provider differences remain explicit behind one common domain boundary.
- Provider Terraform implementations must satisfy the simulation contracts.
- Simulation cannot validate live quotas, availability, identity, or service
  configuration; those checks require separately enabled protected deployment.
