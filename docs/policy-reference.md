# Policy reference

Policy is implemented at two complementary boundaries. Python domain policy
returns stable field-level feedback to API, CLI, and portal. OPA/Rego policy is
validated with pinned Conftest `0.69.0` against sanitized pass/fail deployment
fixtures.

## Common policy

Common rules enforce exact provider selection/match, owner, cost centre, data
classification, positive budget with alerts, sandbox production denial,
private Kubernetes API/nodes, encryption at rest/in transit with key rotation,
central/audit/control-plane logging, least privilege, and the exact GitHub
issuer. Federation subjects cannot contain wildcards.

## AWS policy

AWS rules require private EKS, private nodes, KMS secrets encryption,
CloudTrail with validation, KMS-encrypted/public-blocked S3 state, audience
`sts.amazonaws.com`, exact repository/Environment subject, and distinct plan,
apply, and destroy roles. `iam:*` is denied.

## Azure policy

Azure rules require private AKS, Azure CNI, Workload Identity, Key Vault purge
protection/private access, Activity Log, HTTPS/private state storage, exact
GitHub issuer and repository/Environment subject, and distinct plan, apply, and
destroy identities.

`scripts/check-terraform-policy.sh` validates the four roots and policy fixtures
locally without provider credentials. Passing policy proves the configuration
contract, not live cloud compliance.
