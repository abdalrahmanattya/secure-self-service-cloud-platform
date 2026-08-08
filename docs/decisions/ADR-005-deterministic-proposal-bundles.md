# ADR-005: Use deterministic proposal bundles

- **Status:** Accepted
- **Date:** 2026-08-08

## Context

The same environment request must produce the same reviewable intent through
the API, CLI, portal, and provider adapter. Timestamps, map ordering, random
names, local credentials, and cloud reads must not change the request identity.
Reviewers also need to distinguish a specification change from a plan or
deployment event.

## Decision

Normalize the request into canonical data, calculate a SHA-256 specification
fingerprint, derive a stable request ID, sort policy/resource collections, and
place sanitized generated inputs in a deterministic proposal bundle. Keep
timestamps, author, pull-request links, workflow evidence, backend state, and
plan hash outside local proposal state. The proposal ID is derived from the
canonical request plus installation/provider/mode/schema identity; the content
hash also covers every generated artifact.

Bundles exclude credentials, state, saved plans, secrets, and real provider
identifiers. A plan is separately bound to exact source commit, provider lock,
state snapshot, and saved-plan hash.

## Consequences

Review, retries, API/CLI/portal equivalence, and audit correlation become
straightforward. Reproducibility requires pinned tools and reviewed policy
changes. A deterministic bundle does not guarantee a cloud plan is unchanged;
provider state and external data remain separate evidence.

## Alternatives rejected

- generating names from wall-clock time or random values;
- letting each interface define its own request identity; and
- treating a saved plan or state file as public proposal content.
