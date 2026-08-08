# API reference

The FastAPI application uses one process-local `PlatformService`. It exposes
OpenAPI-typed installation, request, proposal, health, version, and metrics
routes. Restarting the process clears all records.

## Proposal endpoints

| Method | Endpoint | Behavior |
| --- | --- | --- |
| `POST` | `/v1/deployment-proposals` | Create or return the canonical proposal for an accepted stored request |
| `GET` | `/v1/deployment-proposals` | List proposals sorted by proposal ID |
| `GET` | `/v1/deployment-proposals/{proposal_id}` | Read one immutable proposal or return `404` |

Create requires `Idempotency-Key` and this body:

```json
{
  "request_id": "env-0123456789abcdef"
}
```

Successful creation and idempotent retries return HTTP `201`. Missing/blank
idempotency keys return `400`; reusing a key for another request returns `409`;
unknown request/proposal IDs return `404`; denied requests or request CIDRs that
cannot supply provider subnets return a typed proposal-not-allowed error.

## Proposal response

The response contains:

- schema version `proposal.v1`;
- stable `proposal-<16-hex>` ID and 64-character content hash;
- request ID/fingerprint and installation ID;
- provider and mode inherited from the active installation;
- state `ready_for_review`; and
- seven sorted textual artifacts.

`ready_for_review` means deterministic evidence is available. It does not mean
a pull request exists or that GitHub approval, plan, apply, drift, rollback, or
destroy occurred. Protected GitHub approval is external to API state.

## Complete endpoint set

See [shared interfaces](../interfaces.md) for installation/request routes and
idempotency. The API deliberately has no plan, apply, rollback, drift, destroy,
cloud credential, or provider SDK endpoint.
