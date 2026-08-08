# Secure Self-Service Cloud Platform

A portfolio-grade internal developer platform for requesting secure,
policy-compliant Kubernetes environments on either Amazon Web Services or
Microsoft Azure.

An administrator selects exactly one cloud provider when installing the
platform. Developers then use a web portal, REST API, or CLI to submit a small
environment request. The platform validates the request, evaluates governance
policies, and returns a deterministic provider simulation through all three
interfaces. Real infrastructure changes are not part of the current demo.

> **Project status:** Milestones 3–5 are complete. The repository now includes
> deterministic AWS and Azure simulation adapters, a shared FastAPI and CLI
> service, and a React portal. The implementation remains credential-free and
> simulation-only; proposal generation, Terraform execution, cloud bootstrap,
> and deployment are future work.

## The problem

Creating a cloud environment usually requires knowledge of networking,
Kubernetes, identity, encryption, logging, policy, cost controls, Terraform,
and CI/CD. When every application team solves those concerns independently,
security and operational standards drift.

This project makes the approved path reusable:

```text
Developer request
      |
      v
Portal / API / CLI
      |
      v
Validation + policy
      |
      v
Deterministic provider simulation
      |
      +----> AWS installation
      |
      +----> Azure installation
```

The software supports both providers, but one installation manages only its
selected provider. It is not a hybrid-cloud deployment system.

## Implemented in Milestones 3–5

- Deterministic AWS simulation for VPC/private networking, EKS 1.36, IAM/IRSA,
  KMS, secrets, logging, detection, and budgets.
- Deterministic Azure simulation for VNet/private networking, private AKS 1.36
  with Azure CNI, Entra RBAC and Workload Identity, Key Vault, monitoring,
  Policy, Defender, private endpoints, and budgets.
- One provider-locked installation and one shared `PlatformService` used by
  the FastAPI API and Typer CLI.
- FastAPI routes for local health, installation readiness, provider/mode
  discovery, and idempotent environment request evaluation.
- A React, TypeScript, Material UI portal with setup, dashboard, request,
  policy feedback, and readiness views.
- Stable request IDs, fingerprints, policy violations, and simulation resource
  descriptions across API, CLI, and portal paths.

The sandbox and enterprise modes are configuration descriptions only. They do
not execute requests in this demo. GitHub proposals, Terraform modules and
plans, apply/destroy workflows, cloud bootstrap, OIDC deployment identities,
and real provider operations are not implemented.

## Safety boundary

The initial implementation is credential-free simulation only. It must not
contact AWS or Azure, create remote state, or incur cloud cost. Future bootstrap,
plan, apply, destroy, and account configuration require an explicit operator
decision and are designed to use short-lived identity rather than static keys.

Never commit credentials, Terraform state, saved plans, private variable files,
or real deployment configuration.

## Documentation

Start with the [local simulation quickstart](docs/simulation-quickstart.md) and
[documentation index](docs/index.md), then review the
[architecture](docs/architecture.md) and the decision to
[select one provider per installation](docs/decisions/ADR-001-one-provider-per-installation.md),
then explore the [shared interfaces](docs/interfaces.md),
[provider adapters](docs/providers/aws.md), and
[domain model and contracts](docs/domain-model.md).

## License

This project is available under the [MIT License](LICENSE).
