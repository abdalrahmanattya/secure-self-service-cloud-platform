# Documentation

The Secure Self-Service Cloud Platform gives development teams a consistent,
reviewable way to request Kubernetes environments on a platform installation
configured for either AWS or Azure.

Milestones 3–5 are complete for the local simulation path: both provider
adapters, the shared API/CLI service, and the React portal are implemented.
This documentation does not imply that a proposal, Terraform plan, apply,
destroy, or cloud deployment exists; those are future capabilities.

## Start here

- [Simulation quickstart](simulation-quickstart.md)
- [Product overview](product-overview.md)
- [Architecture](architecture.md)
- [Shared interfaces](interfaces.md)
- [Provider selection](provider-selection.md)
- [AWS simulation adapter](providers/aws.md)
- [Azure simulation adapter](providers/azure.md)
- [Architecture decisions](decisions/README.md)

## Available documentation

The Start here section covers the currently implemented product, interfaces,
provider simulations, and architecture decisions.

## Future documentation areas

Provider bootstrap, Terraform proposals, protected deployment, rollback, drift,
destroy, and incident runbooks will be added with their implementations.
Until then, sandbox and enterprise pages describe design intent only, while the
quickstart and interface guides document the available credential-free demo.
