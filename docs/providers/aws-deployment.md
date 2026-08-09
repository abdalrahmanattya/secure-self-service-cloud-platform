# AWS sandbox and enterprise design

![AWS sandbox, enterprise, and identity](../diagrams/rendered/aws-topology.svg)

The AWS adapter is a deterministic simulation. The AWS root/modules, bootstrap,
policy fixtures, and protected workflow path are implemented and locally
validated without contacting AWS.

Start with the
[administrator deployment guide](../administrator-deployment-guide.md) for the
full deployment boundary and prerequisite sequence.

## Expected resources created by Terraform

![Expected AWS bootstrap, account, VPC, subnet, EKS, identity, audit, and budget resources](../diagrams/rendered/aws-deployed-resources.svg)

The upper account structure is administrator-owned. The Terraform environment
root creates resources only inside one selected target account:

- one VPC, Internet gateway, public egress subnets, and private subnets across
  the configured Availability Zones;
- public/private route tables, one NAT gateway in sandbox or one per
  Availability Zone in enterprise, and associated Elastic IP addresses;
- an S3 gateway endpoint plus private interface endpoints for ECR, CloudWatch
  Logs, and STS;
- a private-endpoint EKS cluster, managed node group, cluster/node IAM roles,
  KMS secret encryption, and control-plane logging;
- an encrypted/versioned audit S3 bucket, multi-region CloudTrail, KMS key,
  and CloudWatch log group; and
- a monthly AWS Budget and email notifications.

The separate bootstrap root creates the encrypted/versioned Terraform state
bucket and distinct GitHub OIDC roles for plan, apply, and destroy. Exact
resource counts and names come from the reviewed Terraform plan.

## Sandbox

One non-production AWS account contains the implemented VPC, private EKS API
and nodes, controlled egress, KMS encryption, CloudWatch/CloudTrail diagnostics,
and AWS Budget. GuardDuty, Security Hub, application Secrets Manager usage, and
request-expiry automation are expected organizational integrations; the
current environment root does not create them. The account has one approved
region, small cluster tiers, and mandatory owner/cost tags. Production is
rejected by policy.

The sandbox's blast radius is intentionally bounded: no cross-account trust,
no public Kubernetes endpoint, no unmanaged long-lived deployment key, and a
separate destroy approval path.

## Enterprise

The reference landing zone separates management, security, log archive,
network, shared services, development, test, and production accounts. A
network account owns shared connectivity and controlled egress; a log archive
receives immutable audit copies; shared services hosts the platform control
plane. Environment accounts receive only the roles and network paths needed by
their workload.

Production has stricter approval, larger availability-zone redundancy, and
independent budgets. It never shares Terraform state with sandbox or another
provider installation.

## Identity and deployment path

GitHub Actions exchanges its job OIDC token for a narrowly scoped AWS IAM role.
The role is restricted by repository, workflow, ref/environment, audience, and
permissions boundary. Separate plan, apply, and destroy roles are implemented;
apply is available only to a protected Environment after exact-commit and saved-plan
checks. Human SSO is used for bootstrap and emergency break-glass, not stored
in CI.

The root implements one environment stack. The full multi-account enterprise
landing zone remains operator-owned architecture and is not created by this
repository.

See [authentication and OIDC](../authentication-oidc.md), [Terraform modules](../terraform-modules.md),
and [protected deployment](../operations/deployment.md).
