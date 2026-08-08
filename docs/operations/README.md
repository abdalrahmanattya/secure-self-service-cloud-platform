# Operations

These runbooks describe the implemented protected workflow definitions and the
operator procedures around them. The definitions are locally validated but
disabled/unconfigured; no real provider has been operated.

- [Protected deployment](deployment.md)
- [Drift management](drift.md)
- [Rollback](rollback.md)
- [Destroy and expiry](destroy.md)
- [Incident response](incidents.md)
- [Troubleshooting](troubleshooting.md)

## Operating principles

- Treat every change as an auditable proposal with an exact commit and plan
  hash.
- Prefer read-only diagnosis and reversible action.
- Stop at provider, state, identity, budget, or approval mismatch.
- Keep AWS and Azure runbooks distinct after the shared decision points.
- Record what was observed, who approved it, what changed, and how health was
  verified.
