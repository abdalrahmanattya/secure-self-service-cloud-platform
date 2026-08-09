# Terraform implementation reference

AWS and Azure are independent Terraform implementations with separate
providers, roots, modules, backends, tests, bootstrap, identity, and state. No
root combines providers. Local validation pins Terraform `1.15.8`, AWS provider
`6.57.1`, AzureRM `5.0.1`, and AzureAD `3.9.0`, then runs format,
backend-disabled init, validate, and mocked `terraform test` for all four roots.

## Root stacks

| Root | Purpose | v1.0.0 status |
| --- | --- | --- |
| `infrastructure/terraform/aws` | VPC, security/logging, private EKS, budget | implemented and mock-tested; never applied |
| `infrastructure/terraform/azure` | resource group, VNet, security/logging, private AKS, budget | implemented and mock-tested; never applied |
| `infrastructure/terraform/aws-bootstrap` | KMS/S3 state and environment-bound plan/apply/destroy IAM OIDC roles | one-time operator root; not run |
| `infrastructure/terraform/azure-bootstrap` | versioned Blob state and environment-bound plan/apply/destroy identities | one-time operator root; not run |

The main roots consume only the selected proposal's allowlisted
`.auto.tfvars.json`. Provider identifiers, backend coordinates, role/client IDs,
tenant/subscription IDs, and notification addresses remain protected runtime
configuration.

## Modules

| AWS | Azure | Responsibility |
| --- | --- | --- |
| `network` | `network` | private-first network and controlled egress |
| `security-logging` | `security-logging` | encryption, audit, diagnostics, security monitoring |
| `eks-platform` | `aks-platform` | private Kubernetes and managed worker capacity |
| `budget-guardrails` | `budget-guardrails` | monthly budget and notifications |
| `github-oidc` | `github-oidc` | separate environment-bound lifecycle identities |
| `bootstrap` | `bootstrap` | encrypted/versioned state and identity composition |

AWS state uses a KMS-encrypted, versioned, public-blocked S3 bucket and native
S3 backend lockfile support. Azure state uses HTTPS-only, infrastructure-
encrypted, versioned Blob storage with deletion retention and private endpoint/
DNS by default; temporary trusted bootstrap access must be explicit.

## Proposal variables

AWS proposals materialize `region`, `mode`, `name_prefix`, `vpc_cidr`, two
private/two public subnet CIDRs, desired nodes, and monthly USD budget. Azure
proposals materialize `location`, `mode`, `name_prefix`, VNet address space,
two private subnet prefixes, desired nodes, and monthly EUR budget. Real tenant,
subscription, backend, identity, and alert values are never generated from a
developer request.

The roots are real-capable definitions, but no provider authentication,
bootstrap, remote state creation, plan, apply, drift, rollback, or destroy was
performed for this release.
