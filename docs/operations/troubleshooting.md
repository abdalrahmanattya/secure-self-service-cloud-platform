# Troubleshooting

## Local simulation

| Symptom | Check | Expected action |
| --- | --- | --- |
| API health fails | process output and `curl /health` | start the local API; no cloud credentials are needed |
| portal cannot load data | API port and Vite proxy | start API first, then portal; inspect browser network errors |
| request is denied | policy code and field | correct the request; denial is a normal deterministic result |
| IDs differ | normalized payload, profile provider/mode, and idempotency key | use the same canonical request and active profile |
| CLI file is rejected | profile/request schema and supported region | run `platform setup validate` and fix the typed error |

## Designed workflow diagnosis

- **Proposal differs:** compare canonical request, fingerprint, policy bundle,
  tool versions, and source revision; create a new proposal for any change.
- **Plan/apply mismatch:** stop. Compare commit, provider lock, state version,
  backend key, and saved-plan hash; do not re-plan under approval silently.
- **OIDC denied:** verify the GitHub Environment, deployment ref, exact subject,
  issuer/audience, workflow permissions, and operator-side trust conditions.
- **Environment cannot deploy:** verify required reviewers, self-review
  prevention, branch restrictions, and concurrency settings; repository code
  does not create these settings.
- **Drift detected:** classify and preserve evidence before reconciliation.
- **Destroy blocked:** confirm expiry/ownership/backup/approval controls rather
  than bypassing the workflow.

For a real provider incident, use the [incident response](incidents.md) page and
the provider-specific AWS/Azure design rather than making an ad hoc change.
