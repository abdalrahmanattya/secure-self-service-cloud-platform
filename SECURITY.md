# Security Policy

## Supported versions

The project is pre-release. Security fixes are applied to the current `main`
branch until the first stable release establishes a version support policy.

## Reporting a vulnerability

Do not disclose suspected vulnerabilities in a public issue, discussion, pull
request, or log excerpt. Use GitHub's private vulnerability reporting feature
for this repository when available.

Include:

- the affected component and version or commit;
- reproduction steps that do not expose real credentials or cloud resources;
- potential impact; and
- any suggested mitigation.

## Security boundary

Pull-request checks are credential-free. Real cloud deployment is optional and
must use short-lived GitHub OIDC identity, protected environments, an exact
reviewed plan, and explicit approval. Static cloud access keys are unsupported.

Never commit:

- AWS or Azure credentials;
- Terraform state or saved plans;
- private variable files;
- real account, subscription, tenant, or deployment configuration; or
- authentication private keys and client secrets.
