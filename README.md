# Secure Self-Service Cloud Platform

A portfolio-grade internal developer platform for requesting secure,
policy-compliant Kubernetes environments on either Amazon Web Services or
Microsoft Azure.

An administrator selects exactly one cloud provider when installing the
platform. Developers then use a web portal, REST API, or CLI to submit a small
environment request. The platform validates the request, evaluates governance
policies, and can produce deterministic review evidence through all three
interfaces. Simulation resources are available locally in simulation mode;
sandbox and enterprise modes are proposal-only until protected deployment is
configured. Real infrastructure changes are not part of the current demo.

> **Project status:** `v1.0.0` release candidate (not published or tagged).
> Simulation, deterministic proposals, provider Terraform validation, policy,
> workflow security checks, containers, and Helm are implemented and locally
> validated. No AWS or Azure account was authenticated, configured, or changed.
> Real workflows remain disabled because `REAL_DEPLOYMENT_ENABLED` is absent or
> false and their protected GitHub Environments and variables require separate
> operator configuration.

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
Request evaluation and provider evidence
      |
      v
Deterministic proposal (ready_for_review)
      |
      v
External protected workflows (disabled/unconfigured)
      |
      +----> AWS root
      +----> Azure root
```

The software supports both providers, but one installation manages only its
selected provider. It is not a hybrid-cloud deployment system.

## Implemented in Milestones 3–7

- Deterministic AWS simulation for VPC/private networking, EKS 1.36, IAM/IRSA,
  KMS, secrets, logging, detection, and budgets.
- Deterministic Azure simulation for VNet/private networking, private AKS 1.36
  with Azure CNI, Entra RBAC and Workload Identity, Key Vault, monitoring,
  Policy, Defender, private endpoints, and budgets.
- One provider-locked installation and one shared `PlatformService` used by
  the FastAPI API and Typer CLI.
- FastAPI routes for local health, installation readiness, provider/mode
  discovery, idempotent environment requests, and deterministic proposal
  creation/list/detail.
- A React, TypeScript, Material UI portal with setup, dashboard, request,
  policy feedback, readiness, proposal evidence, and operations views.
- Stable request IDs, fingerprints, policy violations, and simulation resource
  descriptions across API, CLI, and portal paths.
- Deterministic, content-addressed proposal bundles with provider-specific
  Terraform inputs, safe CLI materialization, and `ready_for_review` state.
- Separate AWS and Azure Terraform roots, modules, operator-run bootstrap roots,
  OPA/Conftest policy, and fail-closed protected lifecycle workflow definitions.
- Non-root API and portal containers plus a security-hardened Helm chart with
  health probes, resources, disruption controls, and default-deny networking.
- Public architecture, deterministic proposal-bundle contract, provider
  deployment designs, security/threat/cost models, operations runbooks, and
  release-candidate evidence checklist.

The real-capable plan, apply, drift, rollback, and two-stage destroy definitions
are deliberately inert by default. They require a private repository, manual
dispatch from the default branch, exact proposal/commit/hash bindings,
independent reviewer input, protected Environment approval, concurrency, and
short-lived OIDC. The repository does not configure those GitHub or provider
settings, and no real workflow has been executed.

All three installation modes can evaluate accepted requests and create a
deterministic `ready_for_review` proposal locally. Simulation is the only mode
that returns mocked provider resources as an executable local demonstration;
sandbox and enterprise create review bundles only. A proposal is evidence for
an operator-controlled workflow, not a cloud operation.

## Safety boundary

Local validation is credential-free and must not contact AWS or Azure, create
remote state, or incur cloud cost. The bootstrap roots are one-time,
operator-run entry points; protected lifecycle workflows use short-lived OIDC
only after that separately approved setup.

Never commit credentials, Terraform state, saved plans, private variable files,
or real deployment configuration.

## Documentation

Start with the [documentation index](docs/index.md), then run the
[local simulation quickstart](docs/simulation-quickstart.md). The
[architecture tour](docs/architecture-tour.md),
[proposal lifecycle](docs/proposal-lifecycle.md), [provider implementations](docs/providers/README.md),
[interface reference](docs/reference/README.md), and [operations runbooks](docs/operations/README.md)
cover the release-candidate boundary. The [diagram index](docs/diagrams/README.md)
and [architecture decisions](docs/decisions/README.md) provide the visual and
decision records behind it.

## License

This project is available under the [MIT License](LICENSE).
