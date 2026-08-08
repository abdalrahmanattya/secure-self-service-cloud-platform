# CLI reference

The Typer CLI uses the same domain, policy, simulation, and proposal builder as
FastAPI. It prints stable compact JSON and has no plan/apply/destroy command.

## Proposal creation

```text
platform request propose REQUEST.yaml --profile PROFILE.json
platform request propose REQUEST.yaml --profile PROFILE.json --output BUNDLE
platform request propose REQUEST.yaml --profile PROFILE.json --output BUNDLE --force
```

The command evaluates the request, rejects policy denials, creates a canonical
proposal, prints its complete JSON, and optionally materializes:

```text
BUNDLE/
├── .platform-proposal.json
├── environments/policies/<request-id>.md
├── environments/proposals/<proposal-id>.md
├── environments/proposals/<proposal-id>.json
├── environments/requests/<request-id>.json
├── environments/requests/<request-id>.yaml
├── environments/terraform/<provider>/<request-id>.json
└── infrastructure/terraform/<provider>/<request-id>.auto.tfvars.json
```

The marker records proposal ID, content hash, and the sorted artifact allowlist.
Without `--force`, existing output is refused. With `--force`, only an exact,
valid, marked proposal bundle can be atomically replaced. Symlinks, unexpected
files, path escape, and current/home/filesystem-root targets fail closed.

## Status

```text
platform request status SAVED_PROPOSAL.json
platform request status REQUEST.yaml --profile PROFILE.json
platform request status REQUEST_OR_PROPOSAL_ID
```

A saved proposal file must be the complete JSON printed by `propose`. A request
file is re-evaluated process-independently with its profile. Bare IDs resolve
only in the same live service process; they are not durable across ordinary
separate CLI/API invocations.

The reported proposal state is `ready_for_review`. GitHub review/approval and
later protected workflow outcomes are external and are not synthesized by the
CLI.
