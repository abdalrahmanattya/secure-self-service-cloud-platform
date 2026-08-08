# ADR-002: Keep the domain provider-neutral and expose adapter ports

## Status

Accepted

## Context

The platform supports AWS and Azure as alternative choices for an installation.
The portal, API, CLI, and policy behavior should remain equivalent regardless
of that choice. If common request models import cloud SDKs or contain
provider-native resource details, provider selection leaks into every consumer
and a request can accidentally target the wrong cloud.

Milestone 2 also needs a useful simulation path before credentials, accounts,
subscriptions, Terraform, or cloud APIs are introduced.

## Decision

The domain layer contains only provider-neutral Pydantic contracts. A raw
environment request has no provider. The provider is resolved from the selected
installation profile and becomes part of the normalized request identity.

The domain exposes a runtime-checkable base `ProviderAdapter` port and explicit
statically narrowed `AWSProviderAdapter` and `AzureProviderAdapter` protocols.
Only the base port is runtime-checkable: structurally identical marker
protocols cannot be distinguished at runtime. Adapters validate the selected
installation, validate the normalized request, and return neutral validation
violations and deterministic simulation resources. The orchestrator validates
common policies first, routes only to the selected provider, then performs
those two adapter validation stages before simulation.

Syntactically valid public and IPv6 networks are accepted by the request model
so the common policy layer can return the stable
`network-must-be-private-ipv4` explanation. Policy and validation contracts are
internally consistent, violations are sorted by code, field, and message with
exact duplicates removed, and simulation resources are sorted deterministically.

Provider SDKs, Terraform modules, credentials, account/subscription IDs, and
network calls belong in later provider-specific layers. They must not be
required to import or test the common domain.

## Consequences

Positive consequences:

- Every future interface can share one validated request and one explanation
  of policy failures.
- Provider lock and request fingerprints make installation ownership explicit.
- Both provider routes can be tested credential-free with fake adapters.
- Provider implementations can evolve independently behind stable ports.
- Simulation remains safe and reproducible for portfolio demonstrations.

Trade-offs:

- Provider-specific capability differences need a separate adapter validation
  result rather than being added to common models.
- The neutral model cannot express every provider feature; provider-native
  configuration must be introduced behind an explicit boundary later.
- Adapter registration needs explicit mismatch and missing-adapter checks.

## Rejected alternatives

### Put AWS and Azure fields in one request model

Rejected because it creates optional-field combinations, leaks provider details
into every interface, and makes provider mismatch easy to introduce.

### Let each interface choose its own provider

Rejected because provider ownership belongs to the installation and must remain
immutable after activation.

### Import cloud SDKs in the common domain

Rejected because it increases dependency and credential surface, prevents
credential-free tests, and couples policy contracts to external APIs.
