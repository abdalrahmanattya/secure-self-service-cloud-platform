# Authentication, bootstrap, and OIDC

The local API/CLI/portal and provider simulations need no cloud credential. The
repository implements one-time operator bootstrap roots and short-lived GitHub
OIDC workflow authentication, but neither has been configured or executed.

## One-time operator bootstrap

An authorized operator runs exactly one provider bootstrap root after separate
approval:

- AWS creates a versioned, KMS-encrypted, public-blocked S3 state bucket plus
  separate plan, apply, and destroy IAM roles with exact Environment subjects
  and audience `sts.amazonaws.com`.
- Azure creates HTTPS-only, versioned, retained Blob state with private access
  by default plus separate plan, apply, and destroy managed identities,
  federated credentials, and scoped custom roles.

Bootstrap is intentionally absent from GitHub Actions. Its real names, network
IDs, tenant/subscription details, and outputs stay outside the repository and
are copied into protected GitHub variables only after review.

## Protected GitHub Environments

The workflow definitions reference `platform-plan`, `platform-apply`,
`platform-drift`, and `platform-destroy`. Operators must create them, require
independent reviewers, prevent self-review, restrict deployment branches/tags
to approved protected refs, and review Environment variables. Repository code
cannot configure these settings.

Each workflow has a provider/mode/operation concurrency group and disables
in-progress cancellation. The destroy plan and destroy apply share the same
group. Operators must also prevent unsafe overlap across lifecycle operations
for the same installation/state boundary.

## Required runtime variables

`REAL_DEPLOYMENT_ENABLED` is a fail-closed repository variable and remains
absent or false in this RC. The real-capable jobs also require a private
repository and the default branch.

| Provider | Protected variables |
| --- | --- |
| AWS | `AWS_TF_STATE_BUCKET`, `AWS_TF_STATE_REGION`, `AWS_PLAN_ROLE_ARN`, `AWS_APPLY_ROLE_ARN`, `AWS_DESTROY_ROLE_ARN` |
| Azure | `AZURE_TF_STATE_RESOURCE_GROUP`, `AZURE_TF_STATE_STORAGE_ACCOUNT`, `AZURE_TF_STATE_CONTAINER`, `AZURE_PLAN_CLIENT_ID`, `AZURE_APPLY_CLIENT_ID`, `AZURE_DESTROY_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID` |

Plan/drift use the plan identity, apply/rollback use the apply identity, and
destroy-plan/destroy-apply use the destroy identity. Because OIDC subjects are
Environment-bound, operators must verify an exact trust/federated credential
for every Environment from which an identity is used, including
`platform-drift`; a broad repository wildcard is forbidden.

## Exact federation contract

```text
GitHub issuer: https://token.actions.githubusercontent.com
AWS audience: sts.amazonaws.com
AWS subject: repo:<owner>/<repository>:environment:<environment>
Azure audience: api://AzureADTokenExchange
Azure subject: repo:<owner>/<repository>:environment:<environment>
```

No static AWS key, Azure client secret, service-principal password, or cloud
profile belongs in GitHub. OIDC tokens are requested only inside protected
jobs. These operator configuration requirements are not proof that trust exists
in a real account or tenant.
