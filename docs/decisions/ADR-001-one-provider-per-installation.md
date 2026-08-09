# ADR-001: Select one cloud provider per installation

- **Status:** Accepted
- **Date:** 2026-08-08

## Context

The platform should be useful to organizations that operate on AWS or Azure.
Running both providers from one installation would introduce cross-cloud
identity, networking, state, incident, and consistency concerns that are not
required to serve either organization well.

## Decision

The software supports AWS and Azure, but an administrator selects exactly one
provider when activating an installation. The choice is recorded in the
installation profile and becomes immutable after state, requests, or proposals
exist.

Common domain behavior and governance outcomes are shared. Provider adapters,
Terraform modules, policies, bootstrap, identity, state, and deployment remain
provider-native and separate.

Changing provider requires a separate installation and state backend. The
platform does not migrate or synchronize environments across clouds.

## Consequences

### Benefits

- Each installation has one clear identity and trust boundary.
- AWS and Azure can use their native security and operational services.
- Requests cannot accidentally target the wrong provider.
- The design avoids implying unsupported cross-cloud disaster recovery.

### Costs

- Provider implementations and tests are maintained separately.
- Organizations using both clouds need two platform installations.
- Equivalent outcomes may have different configuration and operating models.

## Alternatives considered

- **Hybrid installation:** rejected because it expands identity, networking,
  failure, and state complexity without being required by the product goal.
- **AWS-only or Azure-only codebase:** rejected because provider choice is a
  core product requirement.
- **Provider switching in place:** rejected because existing state and cloud
  resources cannot be safely reinterpreted as another provider.
