# Provider Selection

The platform supports both Amazon Web Services (AWS) and Microsoft Azure,
but each installation uses exactly one provider. The administrator chooses
the provider during initial setup, and every environment request inherits that
choice.

This is a provider choice, not a per-request deployment target. A developer
does not select AWS or Azure while requesting an environment. The platform
profile already defines where that installation is allowed to operate.

## Choose one provider at installation

The installation wizard presents two choices:

```text
AWS installation    -> AWS accounts, EKS, IAM, KMS, CloudWatch
Azure installation  -> Azure subscriptions, AKS, Entra ID, Key Vault, Monitor
```

The administrator then selects the operating mode:

- Simulation for local, credential-free demonstrations.
- Sandbox for restricted use in one AWS account or Azure subscription.
- Enterprise for separated account or subscription boundaries.

The resulting installation profile records the selected provider, mode, and
the configuration references needed for that provider. The profile is
validated before it becomes active.

## Why the provider is locked

Provider locking prevents one state backend, proposal history, or deployment
workflow from being interpreted against the wrong cloud.

Once an installation is activated, the provider cannot be changed in place.
The platform rejects:

- AWS requests in an Azure installation.
- Azure requests in an AWS installation.
- A provider change after proposals or state exist.
- Mixed AWS and Azure account or subscription configuration.
- A deployment workflow whose provider does not match the active profile.

To use the other provider, the administrator creates a separate installation
with its own profile, state backend, identity configuration, and deployment
history. This makes the boundary visible and protects the audit trail.

## Common outcomes, provider-native implementation

AWS and Azure use different services and terminology. The platform therefore
shares the desired outcome and policy contract while keeping Terraform modules
and provider adapters separate.

| Desired outcome | AWS implementation | Azure implementation |
| --- | --- | --- |
| Cloud network | VPC, subnets, route tables | VNet, subnets, route tables |
| Managed Kubernetes | Amazon EKS | Azure Kubernetes Service (AKS) |
| Human and workload identity | IAM, IAM Identity Center, IRSA | Entra ID, Azure RBAC, Workload Identity |
| Encryption and key management | AWS KMS | Azure Key Vault and managed keys |
| Application secrets | AWS Secrets Manager | Azure Key Vault |
| Central operational logs | CloudWatch, CloudTrail, S3 archive | Azure Monitor, Log Analytics, Activity Log |
| Configuration governance | AWS Config | Azure Policy |
| Threat and security posture | GuardDuty and Security Hub | Defender for Cloud |
| Cost controls | AWS Budgets and mandatory tags | Cost Management budgets and resource tags |
| Private service access | VPC endpoints | Private Endpoints |
| GitHub federation | IAM OIDC provider and roles | Entra workload identity federation |
| Terraform state | Encrypted, versioned S3 storage | Encrypted Azure Blob Storage |

The table maps outcomes, not interchangeable resource definitions. For
example, a private Kubernetes control plane is enforced through EKS settings
on AWS and AKS settings on Azure. A policy failure is presented in common
language, while the diagnostic identifies the provider-specific control.

## AWS profile

An AWS profile uses AWS accounts, regions, and provider-native identity and
security services.

The reference defaults are:

- Region `eu-west-1`.
- EKS Kubernetes version `1.36`.
- A private EKS API and private worker nodes.
- KMS encryption and complete control-plane logging.
- Development and test across two availability zones with one NAT gateway.
- Production across three availability zones with one NAT gateway per zone.

Enterprise AWS installations separate management, security, log archive,
network, shared services, development, test, and production accounts. Sandbox
installations use one account and cannot create production environments.

The AWS implementation is organized into separate modules for networking,
security and logging, EKS, GitHub OIDC, budgets, and bootstrap. Real account
IDs, role ARNs, state references, and other private values are supplied
through protected configuration.

## Azure profile

An Azure profile uses an Azure tenant, subscriptions, regions, and
provider-native identity and security services.

The reference defaults are:

- Primary region `northeurope`.
- An approved AKS Kubernetes `1.36` release where supported.
- A private AKS cluster and private nodes.
- Azure CNI, Workload Identity, Key Vault integration, and diagnostic settings.
- Sandbox controlled NAT egress in one subscription.
- Enterprise hub-and-spoke networking with centralized controlled egress.

Enterprise Azure installations use a tenant and management-group hierarchy
with management, connectivity, identity, shared services, development, test,
and production subscriptions. Sandbox installations use one subscription and
cannot create production environments.

The Azure implementation is organized into separate modules for networking,
security and logging, AKS, GitHub federation, budgets, and bootstrap. Real
subscription IDs, tenant references, role assignments, state references, and
other private values are supplied through protected configuration.

## Configuration boundaries

The platform separates information that describes a requested environment from
information that grants access to a cloud.

### Request configuration

Developers provide values such as:

- Application and environment name.
- Owner and cost centre.
- Data classification.
- Region and network CIDR.
- Cluster size.
- Monthly budget.
- Business justification.
- Expiry date for non-production.

The provider is resolved from the active installation profile. Accepted
requests are normalized and stored under
`environments/requests/<request-id>.yaml`.

### Deployment configuration

Administrators provide protected references such as:

- AWS account IDs or Azure subscription IDs.
- AWS role ARNs or Azure identity and role-assignment references.
- Tenant or organization configuration.
- Terraform state storage.
- KMS or Key Vault references.
- GitHub Environment and OIDC settings.
- Budgets and provider-specific prerequisites.

These values are not placed in public examples, committed Terraform variable
files, saved plans, or application logs. Initial simulation does not require
any of them.

## Provider selection by mode

| Mode | AWS | Azure | Real cloud access |
| --- | --- | --- | --- |
| Simulation | Mock AWS behavior | Mock AzureRM and AzureAD behavior | None |
| Sandbox | One AWS account; production forbidden | One Azure subscription; production forbidden | Optional, protected |
| Enterprise | Separated AWS accounts | Tenant, management groups, and separated subscriptions | Optional, protected |

The mode changes the configuration and policy requirements, but it does not
allow a second provider to be added to the installation.

## Why this is not hybrid cloud

Hybrid cloud means a single operating design intentionally runs or coordinates
workloads across more than one cloud at the same time. This platform does not
do that.

Instead:

```text
Installation A: AWS profile  -> AWS environments only
Installation B: Azure profile -> Azure environments only
```

The platform shares product concepts such as environment requests, policy
decisions, proposals, budgets, and audit history. It does not share a
deployment state, cluster, network, identity boundary, or Terraform module
between AWS and Azure.

Supporting both providers means the product can be installed by an AWS-based
organization or an Azure-based organization. It does not mean one installation
will place a single environment across both clouds.

## Changing provider later

Changing provider is a migration to a new installation, not an edit to the
existing profile. The safe sequence is:

1. Export the provider-independent request and audit information that should
   be retained.
2. Complete or explicitly close the existing provider's environments.
3. Create a new installation profile for the other provider.
4. Configure its separate identity, state, budgets, and provider prerequisites.
5. Validate the new profile in simulation mode.
6. Re-submit approved requests to generate provider-specific proposals.

This preserves the old provider's history and prevents a change of cloud from
silently changing the meaning of existing Terraform state.

## Deployment safeguards

Provider selection is checked at every important boundary. A protected real
deployment requires exact default-branch proposal inputs, an exact commit,
matching request/proposal/provider/mode, verified input/plan hashes,
independent review, and protected Environment approval. The workflow also verifies that the
provider in the proposal matches the active installation profile.

Real deployments use short-lived AWS or Azure OIDC credentials after an
explicit bootstrap. Static cloud access keys are not supported.
