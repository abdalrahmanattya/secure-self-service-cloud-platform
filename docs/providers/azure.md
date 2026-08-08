# Azure simulation adapter

The Azure adapter is the provider-specific simulation boundary for an Azure
installation. It implements the provider-neutral `AzureProviderAdapter` port
and returns immutable `SimulationResource` descriptions. The adapter is
available to the application as
`secure_cloud_platform.providers.azure.AzureSimulationAdapter`; Azure-specific
implementation details are not exported through the provider-neutral package
root.

## Boundary and no-cloud guarantee

The adapter itself is simulation-only. It does not import Azure SDKs,
Terraform, Azure CLI, AzureRM, AzureAD, or any other cloud client. It does not
read credentials or environment variables, make DNS or HTTP requests, inspect
an Azure tenant or subscription, create resources, reserve capacity, or
calculate a live price. Its output is a deterministic design description for
review and testing.

The descriptions contain no tenant IDs, subscription IDs, resource IDs,
credentials, access tokens, private endpoint addresses, or other
provider-generated identifiers. Names are local correlation labels derived
from the normalized application name and request ID; they are not Azure
resources.

## Validation

The adapter fails closed. Installation validation requires the immutable
profile provider to be `azure` and requires every configured allowed region to
be in this sanitized set:

`northeurope`, `westeurope`, `eastus`, `westus2`

An allowed-region list containing a mixture of supported and unsupported
values is rejected as a whole. Request validation likewise requires the
resolved provider to be Azure and the request region to be in the same set.
Provider failures use neutral `PolicyViolation` objects with stable
`azure-*` codes, a domain field, and a message suitable for a portal, API, CLI,
or pull-request summary. A rejected installation or request must not proceed
to simulation through the normal orchestration path.

## Simulated resources and security controls

For an accepted resolved request, the adapter returns exactly eight resource
descriptions. They express the intended secure sandbox or enterprise-ready
shape without pretending that deployment has occurred.

| Kind | Simulated controls |
| --- | --- |
| `azure-vnet` | Private subnets, network security groups, and controlled egress for the request CIDR. |
| `azure-aks` | AKS 1.36, Azure CNI, private API server, and private nodes. |
| `azure-entra` | Azure RBAC, managed identity, and Entra Workload Identity. |
| `azure-key-vault` | Encryption at rest, soft delete, purge protection, and private access. |
| `azure-monitor` | Azure Monitor diagnostics, Log Analytics, and Activity Log collection. |
| `azure-policy` | Azure Policy, Defender for Cloud, and denial of public access. |
| `azure-private-endpoints` | VNet-private paths for AKS, Key Vault, and monitoring services. |
| `azure-budget` | Environment-scoped monthly budget from the request and 80%/100% alerts. |

Resource names use lowercase letters, numbers, and hyphens. Each includes a
bounded sanitized application slug, the normalized `env-` request ID, and a
resource suffix, so repeated simulation of the same request produces the same
names and attributes. The request's normalized network CIDR and monthly
budget are carried only as neutral simulation attributes.

## Defaults and operating modes

The common domain defaults to simulation mode and requires an explicit provider
selection before activation. Azure's simulation defaults are:

- region: `northeurope` when selected in installation guardrails;
- Kubernetes: AKS `1.36` with Azure CNI;
- cluster exposure: private API server and private nodes;
- identity: Entra RBAC and Workload Identity using managed identity concepts;
- protection: Key Vault-backed encryption, private access, Policy, and
  Defender for Cloud;
- operations: Azure Monitor, Log Analytics, and Activity Log diagnostics;
- networking: VNet-private service paths with controlled egress; and
- cost: the request's monthly budget with 80% and 100% alert thresholds.

Sandbox and enterprise resource shapes are implemented in the separate Azure
Terraform root and modules. The simulation adapter itself remains credential-
free and contacts neither mode. Full hub-spoke/multi-subscription landing-zone
configuration remains operator-owned.

Azure bootstrap, state, and protected lifecycle definitions remain separate
from this adapter. Their real credentials/subscription configuration and any
execution require explicit operator approval and are absent in this RC.
