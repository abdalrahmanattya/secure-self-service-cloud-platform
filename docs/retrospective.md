# Milestones 6–7 retrospective

## What the v1.0.0 release demonstrates

- One provider-locked product model can serve AWS and Azure without pretending
  their resource and identity models are interchangeable.
- Deterministic normalization and stable policy feedback make API, CLI, portal,
  and proposal review explain the same request.
- A GitHub review boundary creates a useful separation between requesting an
  environment and changing a cloud account or subscription.
- Simulation gives a reproducible local evaluation without credentials or cost.
- Provider-specific Terraform roots, OPA policy, protected workflow guards,
  containers, and Helm can be validated without authenticating to a provider.

## What remains deliberately outside the demo

The release does not claim live cloud validation. Terraform modules, bootstrap,
remote state, OIDC trust, protected plan/apply, drift, rollback, and destroy are
implemented as code/definitions but require operator-owned infrastructure and
approval. Proposal state is in memory and GitHub approval remains external.

## Lessons and next validation

The next product increment should add durable proposal/audit persistence and
pull-request publication. A future operator acceptance pass should
prove least privilege, state recovery, budget enforcement, destroy safety,
drift detection, and incident runbooks independently for AWS and Azure.
