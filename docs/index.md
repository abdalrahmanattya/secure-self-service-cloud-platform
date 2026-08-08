# Documentation

The Secure Self-Service Cloud Platform gives development teams a consistent,
reviewable way to request Kubernetes environments on a platform installation
configured for either AWS or Azure.

`v1.0.0` is a release candidate, not a published release. Milestones 3–7 are
implemented and locally validated without credentials: provider simulations,
deterministic proposals, API/CLI/portal flows, Terraform mock tests, policy,
protected workflow definitions, containers, and Helm. No real provider was
authenticated or configured and no cloud operation ran.

## Start here

- [Simulation quickstart](simulation-quickstart.md)
- [Product overview](product-overview.md)
- [Architecture tour](architecture-tour.md)
- [Proposal lifecycle](proposal-lifecycle.md)
- [Architecture](architecture.md)
- [Shared interfaces](interfaces.md)
- [Provider selection](provider-selection.md)
- [Provider designs](providers/README.md)
- [API, CLI, and portal references](reference/README.md)
- [Terraform modules](terraform-modules.md)
- [Runtime containers and Helm](runtime-delivery.md)
- [Policy reference](policy-reference.md)
- [Authentication and OIDC](authentication-oidc.md)
- [State model](state-model.md)
- [Security and threat model](security-threat-model.md)
- [Cost model](cost-model.md)
- [Operations runbooks](operations/README.md)
- [Provider comparison](provider-comparison.md)
- [Portfolio demo](portfolio-demo.md)
- [Retrospective](retrospective.md)
- [Release-candidate checklist](release-candidate-checklist.md)
- [Architecture decisions](decisions/README.md)
- [Diagram index](diagrams/README.md)

## Reading the status labels

Each page identifies whether a path is:

- **Implemented and locally validated:** code or configuration exists and its
  credential-free tests/checks pass.
- **Operator configured:** protected GitHub Environments/variables, provider
  identifiers, bootstrap inputs, and trust settings are not repository defaults.
- **Not executed:** no real credentials, provider API, remote state, resource,
  deployment, or cost is used by this release candidate.

`REAL_DEPLOYMENT_ENABLED` remains absent or false. The release/tag and GitHub
Pages site are not published.
