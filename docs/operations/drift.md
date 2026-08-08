# Drift management

Drift is any observed provider state that differs from the approved proposal,
Terraform state, or policy baseline. The implemented workflow is manual and
read-only (`terraform plan -detailed-exitcode`); it is not scheduled and has
not been run. It uses the plan identity/runtime variables from the separately
protected `platform-drift` Environment.

1. acquire the state/backend read lock and verify provider identity;
2. run a refresh/plan without apply;
3. classify changes as expected, unauthorized, security-relevant, or unknown;
4. create an audit event and notify the owner/security/operations route;
5. reconcile through a new proposal, or isolate and roll back an unauthorized
   change; and
6. update the baseline only after review.

Never overwrite drift by blindly applying an old proposal. If state and
provider observations disagree, preserve both artifacts, block mutation, and
resolve the state-integrity incident first.
