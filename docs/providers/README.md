# Provider deployment designs

AWS and Azure share request semantics and governance outcomes, but they do not
share Terraform modules, state backends, identities, or cloud operations. The
provider adapters are credential-free simulations; separate real-capable
Terraform and bootstrap roots are implemented and mock-validated. The sandbox
and enterprise pages are implementation references, not live deployment reports.

- [AWS simulation adapter](aws.md)
- [AWS sandbox and enterprise design](aws-deployment.md)
- [Azure simulation adapter](azure.md)
- [Azure sandbox and enterprise design](azure-deployment.md)
- [Provider comparison](../provider-comparison.md)

## Operating modes

| Mode | AWS boundary | Azure boundary | Production |
| --- | --- | --- | --- |
| Simulation | mocked provider behavior | mocked provider behavior | represented locally only |
| Sandbox | one account, one region | one subscription, one region | forbidden |
| Enterprise | separated accounts and shared services | tenant/management groups and separated subscriptions | explicitly governed |

Every real mode requires separate operator setup, protected configuration,
short-lived OIDC, remote state, budgets, cleanup ownership, and approval. None
of those real operations is being run for this release candidate.
