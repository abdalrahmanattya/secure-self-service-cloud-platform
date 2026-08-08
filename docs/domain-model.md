# Domain model and contracts

Milestone 2 established the provider-neutral boundary now used by the API,
CLI, portal, policy engine, proposals, and provider implementations. It is deliberately
small: it describes what an installation and environment request mean without
importing an AWS or Azure SDK.

## Installation lifecycle

An installation has one provider, one operating mode, a status, and shared
guardrails. A profile starts as `draft`. An administrator selects AWS or Azure
while it is draft, then activates the profile. Activation locks the provider;
changing the provider on an `active` or `retired` profile raises a typed domain
error. An active profile can be retired, but a retired profile cannot be
reactivated.

```text
draft --select provider--> draft --activate--> active --retire--> retired
  |                          |                    |
  +-- provider may change    +-- provider locked +-- provider locked
```

The lifecycle rule protects state ownership. AWS and Azure are alternative
installation choices, not two targets managed by the same installation.

## Request boundary

The submitted `EnvironmentRequest` intentionally has no provider field. This
prevents a caller from choosing a different cloud in a request. The selected
provider is resolved from the installation profile and produces a
`ResolvedEnvironmentRequest`.

The request contains the common business facts needed by all interfaces:

| Field | Purpose |
| --- | --- |
| application, owner, cost centre | ownership and chargeback |
| environment | development, test, or production intent |
| data classification | handling and protection requirements |
| region and private network CIDR | placement and network boundary |
| cluster size | approved capacity tier |
| monthly budget | cost guardrail |
| business justification | auditable reason |
| non-production expiry | cleanup control for development and test |

Normalization trims and canonicalizes text, accepts syntactically valid IPv4 and
IPv6 networks, normalizes money to two decimal places, and emits deterministic
canonical JSON, a SHA-256 fingerprint, and an `env-<fingerprint-prefix>` request
ID. The common policy layer then gives a friendly
`network-must-be-private-ipv4` denial for public or IPv6 networks. No clock,
random number, credential, or cloud call participates in the identity.

The common guardrail model uses the sanitized placeholder region
`example-region` by default. Deployable installations must provide their own
explicit approved region list; no AWS or Azure region is a common-model
default.

## Policy contracts

Common policy results use stable codes, friendly messages, and field names.
The common evaluator checks:

- the installation is active;
- the request provider matches the installation provider;
- the network is private IPv4;
- the region is allowed;
- the budget and cluster size are within guardrails;
- sandbox mode rejects production; and
- development and test requests have a future expiry within the configured
  lifetime.

The evaluator receives an explicit date so tests and proposals remain
reproducible. Provider adapters return the same neutral violation contract.
Common and provider decisions merge in a stable order, allowing every
interface to show the same explanation.

## Adapter ports

`ProviderAdapter` is the only runtime-checkable port with three neutral concepts:

1. a declared `CloudProvider`;
2. installation validation and request validation returning
   `ProviderValidation`; and
3. deterministic simulation resources.

`AWSProviderAdapter` and `AzureProviderAdapter` are explicit, statically
narrowed protocol names for the two concrete implementations. They are not
runtime-checkable marker protocols because structural runtime checks cannot
distinguish them. They do not expose SDK clients, account IDs, subscriptions,
regions, Terraform resources, or credentials. A registry entry whose key does
not match the adapter declaration is rejected before simulation.

## Simulation orchestration

`SimulationOrchestrator` follows this order:

```text
raw request
    |
    v
resolve provider + normalize identity
    |
    v
common policies -- denied --> outcome with violations
    |
  allowed
    v
installation validation -- denied --> merged outcome with violations
    |
  allowed
    v
request validation -- denied --> merged outcome with violations
    |
  allowed
    v
selected adapter simulation --> deterministic resource result
```

The inactive adapter is never called when common policy denies the request.
Only the selected provider is looked up. Missing or mismatched adapters are
typed failures. Violations are sorted by code, field, and message; exact
duplicates are removed. Simulation resources and their attributes are sorted
deterministically, and simulation is available only to an installation
explicitly configured in `simulation` mode.
