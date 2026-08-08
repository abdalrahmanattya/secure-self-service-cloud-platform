# Portal reference

The React portal implements setup, dashboard, request creation/detail, policy
feedback, readiness, proposal detail, and operations views through its
OpenAPI-generated FastAPI client.

## Proposal flow

An accepted request displays **Create review proposal**. The portal sends
`POST /v1/deployment-proposals` with one browser-generated idempotency key for
the submission attempt, refreshes the proposal list, and navigates to the
proposal detail page.

The proposal page displays:

- `ready_for_review`, provider, and mode chips;
- proposal/request IDs, schema, and content hash;
- the linked request; and
- every artifact path with a bounded content preview.

Denied requests cannot create proposals. The operations page lists all
process-memory proposals and marks GitHub review, protected plan/approval,
apply, drift, rollback, and destroy as external/not executed. It intentionally
offers no cloud lifecycle control.

Restarting the local API clears the operations list. A proposal page therefore
does not establish durable persistence or GitHub approval.
