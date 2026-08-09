# Terraform stacks

AWS and Azure are independent alternatives. Each provider has its own root
stack, provider-specific modules, state backend, lock file, and operator-run
bootstrap root; no root combines AWS and Azure resources.

The `aws-bootstrap` and `azure-bootstrap` roots are intentionally not called
by GitHub Actions. An operator supplies protected names and networking/state
configuration, runs bootstrap after separate approval, and publishes the
resulting plan/apply/destroy identity IDs into protected GitHub Environment
variables. The main platform roots consume proposal var-files and never create
their first workflow identity.

All examples are sanitized. `simulation` is valid for local mock-provider
tests, while protected cloud workflows accept only `sandbox` or `enterprise`.
No bootstrap, plan, apply, destroy, or provider API operation is performed by
the repository quality checks.

Real deployment is an opt-in design for a private repository only. It requires
protected GitHub Environments, protected environment variables, short-lived
OIDC identities, and separate approval; the public source repository remains
disabled by default and must not receive account, subscription, tenant, state,
or credential values.
