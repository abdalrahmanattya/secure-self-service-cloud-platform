# Azure sandbox and enterprise design

![Azure sandbox, enterprise, and identity](../diagrams/rendered/azure-topology.svg)

The Azure adapter is a deterministic simulation. The Azure root/modules,
bootstrap, policy fixtures, and protected workflow path are implemented and
locally validated without contacting Azure.

Start with the
[administrator deployment guide](../administrator-deployment-guide.md) for the
full deployment boundary and prerequisite sequence.

## Expected resources created by Terraform

![Expected Azure bootstrap, subscription, VNet, subnet, AKS, identity, logging, vault, and budget resources](../diagrams/rendered/azure-deployed-resources.svg)

The upper tenant/subscription structure is administrator-owned. The Terraform
environment root creates resources only inside one selected target
subscription:

- one platform resource group, VNet, private subnets, and a Network Security
  Group denying Internet inbound traffic;
- one NAT gateway and static public IP for controlled outbound traffic;
- a private AKS cluster and system node pool using Azure CNI overlay, Entra
  RBAC, OIDC issuer, workload identity, and Azure network policy;
- a Log Analytics workspace with 365-day retention and AKS monitoring;
- a private-access Key Vault with RBAC, soft delete, and purge protection; and
- a resource-group monthly budget and email notifications.

The separate bootstrap root creates the Terraform state storage account and
container, a private endpoint in administrator-supplied network and DNS inputs
for the fail-closed path, and distinct federated identities for plan, apply,
and destroy. The explicitly temporary trusted-bootstrap path can enable
controlled public access instead. Exact resource counts and names come from the
reviewed Terraform plan.

## Sandbox

One non-production subscription contains the implemented private AKS cluster,
Azure CNI network, controlled NAT egress, Key Vault, Log Analytics integration,
and Cost Management budget. Private endpoints beyond bootstrap state, Activity
Log export, Azure Policy, Defender for Cloud, and request-expiry automation are
expected organizational integrations; the current environment root does not
create them. One approved region, small cluster tiers, and mandatory tags are
required. Production is rejected.

## Enterprise

The reference tenant uses management groups and separate management,
connectivity, identity, shared-services, development, test, and production
subscriptions. Hub-spoke networking, centralized egress, private DNS, central
diagnostics, and delegated RBAC make the trust boundaries visible. Shared
services hosts the platform control plane; workloads stay in their environment
subscriptions.

## Identity and deployment path

GitHub Actions uses Entra workload identity federation with repository,
workflow, ref/environment, audience, and subject conditions. Separate plan,
apply, and destroy federated identities limit privilege. Apply is available
only after protected Environment approval, exact-commit verification, saved-plan hash
verification, and preflight budget/policy checks.

Human Entra administration is used for bootstrap and break-glass. No client
secret is stored in GitHub or the public repository.

The root implements one environment stack. The full management-group and
multi-subscription enterprise landing zone remains operator-owned architecture
and is not created by this repository.
