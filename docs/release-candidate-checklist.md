# v1.0.0 release record

`v1.0.0` is the first stable release. Its executable scope is the
credential-free local simulation and deterministic proposal workflow. Real
AWS/Azure deployment remains operator-configured and was not run or certified
for this release.

## Implemented and validated

- [x] AWS and Azure credential-free simulations are executable.
- [x] API, CLI, and portal share deterministic request/policy results.
- [x] Deterministic proposal creation/list/detail is implemented with
  `ready_for_review`, idempotency, content hashes, and process-memory state.
- [x] CLI proposal materialization/status and replacement safety are tested.
- [x] Portal proposal creation/detail and operations views are tested.
- [x] Separate AWS/Azure Terraform and bootstrap roots format, initialize with
  backends disabled, validate, and pass mocked Terraform tests.
- [x] Common/AWS/Azure Rego policies pass pinned Conftest allow/deny fixtures.
- [x] Proposal bridge and protected workflow security contracts are checked.
- [x] API/portal container and Helm security defaults are checked locally.
- [x] Mermaid sources/rendered SVG freshness and public documentation checks
  pass.
- [x] Repository checks reject tracked state, saved plans, generated Terraform
  directories, credentials, and real provider identifiers.

## Known limitations

- Proposal and audit persistence is process-local.
- Automatic proposal pull-request publication is not implemented; the CLI
  materializes a deterministic local bundle for operator-controlled review.

## Operator acceptance before real cloud use

- [ ] Use a private repository for the real-capable workflow installation.
- [ ] Run one approved AWS or Azure bootstrap with protected real inputs.
- [ ] Configure `platform-plan`, `platform-apply`, `platform-drift`, and
  `platform-destroy` with required reviewers, self-review prevention, and
  deployment branch/tag restrictions.
- [ ] Configure and independently review all AWS/Azure backend and identity
  runtime variables, including exact Environment-bound OIDC subjects.
- [ ] Test state encryption, locking, versioning, recovery, retention, and
  access logging in the selected provider.
- [ ] Set `REAL_DEPLOYMENT_ENABLED=true` only after every prerequisite passes
  (it remains absent or false for this release).
- [ ] Run and review a non-production real plan with its sensitive one-day
  artifact retention.
- [ ] Complete approved sandbox apply, drift, rollback, two-stage destroy, and
  provider-specific incident drills.
- [ ] Complete enterprise separation, central logging, budget, and break-glass
  review where enterprise mode is intended.

## Publication gate

- [x] Hosted checks pass on the final publication commit.
- [x] Changelog/version metadata and security scope are approved.
- [x] GitHub Pages is published.
- [x] `v1.0.0` tag and GitHub release are published with explicit approval.
