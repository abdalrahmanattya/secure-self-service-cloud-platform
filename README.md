# Secure Self-Service Cloud Platform

A portfolio-grade internal developer platform for requesting secure,
policy-compliant Kubernetes environments on either Amazon Web Services or
Microsoft Azure.

An administrator selects exactly one cloud provider when installing the
platform. Developers then use a web portal, REST API, or CLI to submit a small
environment request. The platform validates the request, evaluates governance
policies, generates deterministic Terraform inputs, and creates an auditable
GitHub proposal. Real infrastructure changes remain behind protected planning
and approval workflows.

> **Project status:** Milestone 2 common domain contracts and credential-free
> simulation orchestration are implemented. Provider-specific adapters and
> user interfaces are planned next.

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
Deterministic Terraform proposal
      |
      v
GitHub review and protected deployment
      |
      +----> AWS installation
      |
      +----> Azure installation
```

The software supports both providers, but one installation manages only its
selected provider. It is not a hybrid-cloud deployment system.

## Planned capabilities

- Accessible React and TypeScript administration portal
- FastAPI service and automation-friendly CLI
- Simulation, single-account/subscription sandbox, and enterprise modes
- Separate provider-native Terraform implementations for AWS and Azure
- Common and provider-specific OPA policy checks
- Private EKS or AKS clusters with central security and observability controls
- GitHub OIDC with short-lived cloud credentials
- Reviewed plan, approval, rollback, drift, and cleanup workflows
- Searchable architecture, security, cost, API, and operations documentation

## Safety boundary

The initial implementation is credential-free simulation only. It must not
contact AWS or Azure, create remote state, or incur cloud cost. Future bootstrap,
plan, apply, destroy, and account configuration require an explicit operator
decision and are designed to use short-lived identity rather than static keys.

Never commit credentials, Terraform state, saved plans, private variable files,
or real deployment configuration.

## Documentation

Start with the [documentation index](docs/index.md), then review the
[architecture](docs/architecture.md) and the decision to
[select one provider per installation](docs/decisions/ADR-001-one-provider-per-installation.md),
then explore the [domain model and contracts](docs/domain-model.md).

## License

This project is available under the [MIT License](LICENSE).
