# Simulation demonstration

This is a safe, reproducible local workflow for evaluation. It exercises the
implemented simulation and intentionally stops before any cloud boundary.

1. Follow the [simulation quickstart](simulation-quickstart.md).
2. Initialize an AWS simulation profile and run a valid request through CLI.
3. Repeat with Azure to show provider-native deterministic resources.
4. Submit a public-network or over-budget request and show friendly policy
   feedback in the API/portal.
5. Compare the same request ID/fingerprint and policy result across interfaces.
6. Create an API/portal proposal and a CLI materialized bundle; compare the
   stable ID, content hash, `ready_for_review`, and provider variables.
7. Walk through the validated Terraform/policy/workflow/container/Helm
   definitions, identifying which real-capable stages remain disabled/unrun.
8. Use the [v1.0.0 release record](release-candidate-checklist.md) to
   explain evidence, limitations, and the next operator approvals.

## Safety boundary

Simulation is executable locally; no AWS/Azure credential, state backend, cloud
API, resource, or bill is involved. Real deployment requires separate setup and
protected approval.
