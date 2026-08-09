# Secure Self-Service Cloud Platform

`v1.0.0` is the stable portfolio release. The local simulation is executable;
real cloud setup and deployment require separate operator configuration and
approval and have not been run.

The Secure Self-Service Cloud Platform is an internal developer platform for
requesting consistent, governed cloud environments. It combines a friendly
web portal, a REST API, a command-line interface, policy as code, and
provider-specific Terraform modules into one controlled workflow.

The platform supports Amazon Web Services (AWS) and Microsoft Azure. An
administrator selects one provider when the platform is installed. The
installation then creates environments only on that provider. This keeps the
deployment boundary clear while allowing the same product experience to be
used by organizations that standardize on AWS or Azure.

## The problem

Creating a cloud environment normally requires decisions about networking,
Kubernetes, identity, encryption, logging, secrets, budgets, and access. When
each application team makes those decisions independently, the organization
gets inconsistent environments and an uneven security posture.

Typical problems include:

- Kubernetes APIs or worker nodes exposed more broadly than necessary.
- Missing encryption, audit logging, or security monitoring.
- Resources without an owner or cost centre.
- Temporary environments that are never removed.
- Terraform changes applied from an engineer's laptop without a consistent
  review trail.
- Different teams solving the same platform problem in incompatible ways.

This platform makes the approved path easier to follow. A developer describes
the environment they need, while the platform supplies the standard network,
identity, security, operations, and cost controls.

## Who uses it

### Platform administrators

Administrators install the platform, select AWS or Azure, choose the operating
mode, configure provider-specific prerequisites, and approve protected
deployment workflows.

### Application developers

Developers request development, test, or production environments through the
portal, API, or CLI. They provide business and ownership information instead
of hand-writing every Terraform resource.

### Security teams

Security teams define identity, encryption, network exposure, logging, and
least-privilege requirements. Policy checks reject requests that do not meet
those requirements before deployment.

### Operations teams

Operations teams use proposal evidence and runbooks in the local release. A real
installation would add deployment history, provider logs, health, and drift
evidence after operator configuration.

### Finance and governance teams

Finance and governance teams use mandatory ownership, cost-centre, budget,
data-classification, and expiry information to improve cost attribution and
resource accountability.

## Why it is useful

The platform provides a repeatable way to create environments without making
every team become an expert in every cloud service.

- **Consistency:** approved modules produce environments with the same core
  controls.
- **Security:** policy checks catch unsafe configuration before deployment.
- **Speed:** a short request replaces weeks of duplicated platform work.
- **Auditability:** proposals, checks, approvals, and deployment results are
  linked to Git history.
- **Cost visibility:** budgets, tags, owners, and non-production expiry dates
  are part of the request rather than an afterthought.
- **Provider choice:** organizations can use AWS or Azure while keeping one
  self-service experience and separate provider implementations.
- **Safe operations:** real changes require an approved proposal, an exact
  commit, a verified plan, and protected approval.

The portfolio demonstration runs simulation and proposal creation locally. The
protected definitions provide a path to a real AWS or Azure
installation when the administrator has
approved accounts or subscriptions, identity configuration, state storage,
budgets, and cleanup procedures.

## Interfaces

The portal, API, and CLI share the same request model and policy decisions. A
user can choose the most convenient interface without getting different
results.

### Web portal

The portal is designed for users who should not need Terraform knowledge. It
provides:

- An installation wizard for provider and mode selection.
- A guided environment-request form.
- Request detail with field-level policy and simulated resources.
- Proposal creation/detail with IDs, content hash, and artifact previews.
- An operations view listing local proposals and external lifecycle boundaries.
- Platform-readiness and operations views.

The portal explains policy failures beside the affected field and uses plain
language for provider-specific requirements.

### REST API

The API supports automation and integration with internal developer tools. Its
primary responsibilities are installation-profile validation, environment
request processing, proposal creation, status retrieval, health, version, and
metrics endpoints.

Representative endpoints include:

```text
POST /v1/platform/installations
GET  /v1/platform/installation
POST /v1/platform/installation/validate
GET  /v1/platform/providers
GET  /v1/platform/modes
POST /v1/environment-requests
GET  /v1/environment-requests/{request_id}
POST /v1/deployment-proposals
GET  /v1/deployment-proposals
GET  /v1/deployment-proposals/{proposal_id}
GET  /health
GET  /version
GET  /metrics
```

Request and proposal creation are idempotent. The local API has no cloud
credential and does not implement real-mode caller authentication. GitHub
workflow OIDC is a separate deployment identity plane. The API creates local
proposal evidence and has no direct Terraform operation.

### CLI

The CLI supports scripting and terminal-based workflows:

```text
platform setup init --provider aws|azure --mode simulation|sandbox|enterprise
platform setup validate PROFILE
platform setup status

platform request validate REQUEST.yaml
platform request render REQUEST.yaml
platform request propose REQUEST.yaml
platform request status REQUEST_ID
```

The CLI uses the same domain and proposal builder as the API and portal.
`request propose` can safely materialize a deterministic bundle, while
`request status` reads saved proposal/request documents or process-local IDs.
The CLI has no direct Terraform or cloud command.

## Request lifecycle

Every request follows the same evidence-based path:

```text
Portal, API, or CLI
        |
        v
Validate the request schema
        |
        v
Normalize values and calculate a specification hash
        |
        v
Evaluate common and provider-specific policies
        |
        v
Generate deterministic provider-specific Terraform inputs
        |
        v
Create deterministic proposal evidence for review
        |
        v
Run Terraform, policy, security, and documentation checks
        |
        v
Review and merge the proposal
        |
        v
Optionally run a protected real plan and apply
```

An accepted request records its normalized form under
`environments/requests/<request-id>.yaml`. Generated inputs are derived from
that request so the same input produces the same proposal.

The request includes application, environment, owner, cost centre, data
classification, region, network CIDR, cluster size, monthly budget, business
justification, and an expiry date for non-production environments. The
provider is inherited from the installation profile rather than chosen per
request.

The real deployment boundary is deliberately separate from request creation.
A protected workflow requires an exact default-branch commit, matching request
and proposal identifiers, verified proposal/tfvars/plan hashes, independent
review, protected Environment approval, and typed confirmation. The implemented
workflows use short-lived OIDC credentials rather than static cloud keys.

## Operating modes

The administrator selects one mode during installation. The mode controls how
much real provider configuration is required and what environments are
allowed.

### Simulation

Simulation is the default development and demonstration mode.

- No AWS or Azure credentials are required.
- No cloud account, subscription, state backend, or provider API is used.
- No cloud resources or cloud cost are created.
- AWS, AzureRM, and AzureAD behavior is represented with mocked providers.
- Requests produce local validation results and simulated Terraform plans.

Simulation lets a reviewer follow the complete request-to-proposal workflow
with mocked provider resources and without access to a cloud tenant. Sandbox
and enterprise use the same credential-free evaluation and proposal-building
path locally, but do not execute provider resources.

### Sandbox

Sandbox mode is for controlled use in one real provider boundary:

- AWS uses one AWS account.
- Azure uses one Azure subscription.
- Production requests are forbidden.
- One region, limited cluster sizes, a strict budget, and an expiry date are
  required.
- A separate, explicit destroy path is required for cleanup.

The administrator supplies real account or subscription references and
provider identity and state configuration through protected configuration.
Those values are not stored in public request examples or source files.

### Enterprise

Enterprise mode is for organizations that separate security, operations,
shared services, and application environments.

AWS uses management, security, log archive, network, shared-services,
development, test, and production accounts. Azure uses a tenant and
management-group structure with management, connectivity, identity,
shared-services, development, test, and production subscriptions.

Enterprise mode validates that required boundaries are configured and that
security, logging, shared services, and production do not collapse into an
uncontrolled shared account or subscription.

In the local portfolio-release boundary, sandbox and enterprise requests are
proposal-only: they can produce `ready_for_review` bundles, but cloud lifecycle
operations require the separately configured protected GitHub workflows.

## Governance and safety boundaries

Common policies require ownership, cost attribution, data classification,
budgets, encryption, private Kubernetes access, central logging, least
privilege, and non-production expiry. AWS and Azure adapters add their own
provider-native checks, such as EKS/IAM requirements or AKS/Entra and Key
Vault requirements.

The platform does not accept real identifiers in public examples, does not
support static cloud access keys, and does not let the portal, API, or CLI
bypass the GitHub review and protected deployment workflow.

## What the platform creates

The provider-specific modules deliver equivalent outcomes using native cloud
services rather than pretending AWS and Azure are the same:

- A controlled network with private application and cluster resources.
- A managed Kubernetes platform with private access and encrypted secrets.
- Workload identity and restricted administrative access.
- Central audit logs, security monitoring, and retention controls.
- Budgets, mandatory tags, ownership, and operational metadata.
- A reviewed, reproducible Terraform proposal.

The details differ by provider, but the user experience and governance goals
remain consistent.

## Scope and boundaries

This is an internal developer platform and a deployable reference
implementation, not a public cloud service. It does not attempt to run one
workload simultaneously across AWS and Azure. It does not create real cloud
resources during the initial simulation-based development. Real bootstrap,
plan, apply, destroy, credentials, account or subscription configuration, and
cost require separate authorization and operational preparation.
