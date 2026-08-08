# Destroy and expiry

Destroy is more restrictive than apply because it removes resources and can
destroy data. The application has no destroy command; separate manual
destroy-plan and destroy-apply workflows are implemented but disabled/unrun.

## Required controls

- request owner and operations confirm the target and retention requirements;
- production destroy requires platform and service-owner approval;
- the workflow verifies exact provider, environment, state key, and commit;
- backups, snapshots, logs, and legal-retention requirements are checked;
- a typed confirmation repeats the target and irreversible effect;
- concurrency blocks apply/drift during destroy; and
- post-destroy evidence confirms state, alerts, budgets, DNS, identities, and
  secrets were handled according to policy.

Both workflow stages require `DESTROY provider/mode/proposal-id` and
`DESTROY CONFIRMED provider/mode/proposal-id`, independent-review checks,
`platform-destroy`, the destroy identity, exact binding hashes, and their shared
destroy concurrency group. The reviewed destroy plan is retained for one day.

Expired development/test environments enter a review queue. Expiry is not an
unattended production deletion trigger. A failed destroy leaves the state and
incident open for operator recovery; it must not be hidden by deleting state.
