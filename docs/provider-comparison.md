# Provider comparison

The product promises common governance outcomes, not identical cloud
resources. The selected provider controls module names, identity semantics,
state backend, diagnostics, and incident procedures.

| Concern | AWS | Azure | Shared platform contract |
| --- | --- | --- | --- |
| Network | VPC, subnets, endpoints | VNet, private endpoints, hub-spoke | private Kubernetes and controlled egress |
| Kubernetes | EKS | AKS | approved version, private API, encrypted nodes |
| Identity | IAM/Identity Center, IRSA, IAM OIDC | Entra RBAC, Workload Identity, federation | short-lived least-privilege roles |
| Secrets/keys | KMS, Secrets Manager | Key Vault | managed encryption and no repo secrets |
| Audit/security | CloudTrail, Config, GuardDuty, Security Hub | Activity Log, Policy, Defender, Monitor | central logs, alerting, evidence retention |
| State | encrypted/versioned S3 with lock controls | encrypted/versioned Blob with lease locking | one backend per installation and provider |
| Cost | AWS Budgets and tags | Cost Management budgets and tags | budget, owner, cost centre, expiry |
| CI federation | IAM OIDC provider | Entra workload identity federation | GitHub-only protected deployment |

The simulation adapters expose deterministic resource descriptions for these
outcomes. They do not prove that the corresponding cloud resources exist.
