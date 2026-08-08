# ADR-006: Make GitHub the only protected deployment boundary

- **Status:** Accepted
- **Date:** 2026-08-08

## Context

The portal, API, and CLI are convenient request interfaces, but giving any of
them direct cloud credentials would make review and approval bypassable. The
project needs a visible audit trail, exact-commit checks, human approval, and
short-lived provider identity.

## Decision

Only a manually dispatched GitHub workflow using exact proposal inputs from the
default branch may perform a real plan, apply, rollback, or destroy in a
separately approved installation. The workflow
must verify provider/mode/request/proposal/commit/state/plan consistency and
use a protected GitHub Environment with required reviewers, self-review
prevention and deployment branch restrictions. Included workflows serialize by
provider/mode/operation; operators must prevent unsafe cross-operation overlap
for the same installation/state boundary.

The operator configures AWS IAM OIDC trust with audience `sts.amazonaws.com`
and the exact repository/environment subject. The operator configures Azure
Entra federation with the exact GitHub issuer and exact repository/environment
subject. Plan, apply, and destroy identities are separate and least-privilege.

Terraform definitions create cloud trust only when an operator separately runs
the bootstrap root. GitHub Environment protections/variables are operator
configuration and are not created automatically by repository code.

## Consequences

The audit path and approval boundary are explicit, and CI receives short-lived
credentials only after gates pass. Local demos remain credential-free. The
decision adds GitHub and operator setup dependencies and requires recovery when
GitHub or the provider identity service is unavailable.

## Alternatives rejected

- direct `terraform apply` from the portal/API/CLI;
- static cloud keys in repository or GitHub secrets; and
- an unreviewed scheduled apply from drift detection.
