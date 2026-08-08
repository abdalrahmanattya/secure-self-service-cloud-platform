# AWS simulation adapter

The AWS adapter is the provider-specific implementation of the platform's
credential-free simulation boundary. It implements the `AWSProviderAdapter`
port and returns neutral `ProviderValidation` and `SimulationResource` models.
It does not create infrastructure, call AWS APIs, load an SDK, read
credentials, or require an account.

## Boundary and validation

`AWSSimulationAdapter` accepts only a resolved AWS request and an AWS
installation profile. It fails closed when:

- the installation provider is not `aws`;
- an installation allows a region outside `eu-west-1`, `eu-central-1`,
  `us-east-1`, or `us-west-2`; or
- a resolved request is not for AWS or requests a region outside that set.

Provider-specific failures use stable `aws-*` violation codes, including
`aws-provider-mismatch` and `aws-region-unsupported`, with neutral field names
and messages suitable for the API, CLI, portal, and proposal review.
The common policy layer still owns installation activation, private IPv4
networking, budgets, cluster-size guardrails, expiry, and sandbox production
rules.

The adapter does not reject an installation mode by itself. Simulation,
sandbox, and enterprise are valid profile modes at this contract boundary;
the orchestration layer separately requires `simulation` mode for a
credential-free simulation run.

## Simulated resources

An accepted request produces eight deterministic descriptions. The model sorts
resources and attributes, so the output order is stable regardless of adapter
construction details.

| Kind | Simulated controls |
| --- | --- |
| `aws-vpc` | Private subnets, controlled egress, VPC endpoints, and environment topology |
| `aws-eks` | EKS `1.36`, private API endpoint and private nodes, KMS encryption, all control-plane logs |
| `aws-iam` | IAM Roles for Service Accounts (IRSA), least privilege, and no static credentials |
| `aws-kms` | Storage encryption and key rotation for EKS and secrets |
| `aws-secrets-manager` | KMS encryption and non-materialized secret values |
| `aws-cloudtrail` | CloudTrail management events, CloudWatch delivery, and log validation |
| `aws-guardduty` | GuardDuty, Security Hub, and finding aggregation |
| `aws-budget` | Application-scoped monthly budget with 80% and 100% alerts |

Development and test requests use two availability zones and one NAT gateway.
Production requests use three availability zones and one NAT gateway per
availability zone. Names combine the `scp-` prefix, a sanitized application
slug, the normalized
`env-<fingerprint-prefix>` request ID, and a descriptive component suffix.
They are deterministic and contain no account IDs, ARNs, credentials, or real
resource IDs. Budget values come from the normalized request and are rendered
as strings, like every other simulation attribute.

## No-cloud guarantee

This adapter imports only the Python standard library and the platform's
provider-neutral contracts. There is no AWS SDK, network client, environment
variable lookup, credential discovery, account or ARN generation, randomness,
Terraform execution, or cloud call in the implementation. Running its tests
and using the adapter's `simulate` method is therefore safe in a disconnected
development environment and cannot create billable AWS resources.
