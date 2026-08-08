# Contributing

Thank you for improving the Secure Self-Service Cloud Platform.

## Before starting

1. Open or select an issue with clear acceptance criteria.
2. Confirm whether the change affects common behavior, AWS, Azure, or public
   interfaces.
3. Keep real cloud identifiers, credentials, state, and plans outside Git.
4. Prefer the simulation path for development and tests.

## Pull requests

- Keep one understandable outcome per pull request.
- Explain user impact, architecture impact, security impact, cost impact, and
  rollback considerations.
- Add or update tests for changed behavior.
- Update professional documentation when an interface or decision changes.
- Do not mix AWS and Azure resources inside one Terraform module.
- Do not bypass policy or validation checks to make a change pass.

Pull requests merge only after required checks succeed and unresolved review
comments are addressed.

## Commit messages

Use concise, outcome-focused messages such as:

```text
feat: validate installation provider selection
fix: reject production requests in sandbox mode
docs: explain Azure enterprise subscription boundaries
```

## Security

Do not open a public issue for a suspected vulnerability. Follow
[SECURITY.md](SECURITY.md).
