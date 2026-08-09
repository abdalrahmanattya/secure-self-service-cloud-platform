# Secure Self-Service Cloud Platform

A portfolio-grade internal developer platform for requesting secure,
policy-compliant Kubernetes environments on either Amazon Web Services (AWS)
or Microsoft Azure.

Platform administrators choose one cloud provider when installing the
platform. Developers can then use a friendly web portal, REST API, or CLI to
submit a small environment request. The platform normalizes the request,
evaluates governance policies, describes the proposed provider resources, and
creates deterministic evidence for review.

This repository is safe to demonstrate without cloud credentials. The local
simulation does not contact AWS or Azure, create infrastructure, or incur cloud
cost.

> **Status:** `v1.0.0rc1` release candidate. The local simulation, proposal
> generation, Terraform validation, policy checks, protected workflow designs,
> containers, Helm chart, documentation, and diagrams are implemented. No
> release tag has been published and no real cloud environment has been
> deployed.

![Secure Self-Service Cloud Platform system context](docs/diagrams/rendered/system-context.svg)

## Why this project exists

Creating a cloud environment normally requires knowledge of networking,
Kubernetes, identity, encryption, logging, policy, budgets, Terraform, and
CI/CD. When every application team solves those concerns independently,
security and operational standards drift.

This platform turns those concerns into one reusable, reviewable path:

```text
Developer request
      |
      v
Portal / API / CLI
      |
      v
Validation + policy
      |
      v
Provider-specific architecture evidence
      |
      v
Deterministic proposal (ready_for_review)
      |
      v
Protected deployment workflows (disabled until configured)
      |
      +----> AWS Terraform root
      +----> Azure Terraform root
```

The codebase supports both providers, but one installation manages only its
selected provider. It is not a hybrid-cloud deployment system. To manage both
providers, run two separate installations with separate configuration and
state.

## What you can demonstrate

- Select AWS or Azure and lock the installation to that provider.
- Choose simulation, sandbox, or enterprise mode.
- Submit the same environment request through the portal, API, or CLI.
- See friendly policy feedback for unsafe or unsupported requests.
- Inspect deterministic request IDs, fingerprints, resource descriptions, and
  proposal hashes.
- Materialize a review bundle containing normalized requests, policy evidence,
  proposal metadata, and provider-specific Terraform inputs.
- Review separate AWS and Azure Terraform modules and security guardrails.
- Review protected plan, apply, drift, rollback, and two-stage destroy workflow
  designs without executing them.

Simulation is the executable local demonstration. Sandbox and enterprise modes
can evaluate requests and create review proposals locally, but remain
proposal-only until an operator configures protected deployment.

## Quick start

The recommended local setup runs the API and portal from source. It requires no
AWS or Azure credentials.

### 1. Prerequisites

Install:

- Git
- Python 3.13
- Node.js 22 with npm
- `curl` for the health check

The commands below work on macOS and Linux and assume a POSIX-compatible shell.

### 2. Clone the repository

```sh
git clone https://github.com/abdalrahmanattya/secure-self-service-cloud-platform.git
cd secure-self-service-cloud-platform
```

### 3. Install the Python application

From the repository root:

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --requirement requirements/dev.txt
```

This installs the FastAPI service, the `platform` CLI, and the development
tools in an isolated virtual environment.

### 4. Install the portal dependencies

Still from the repository root:

```sh
cd web
npm ci
cd ..
```

`npm ci` installs the exact versions recorded in `web/package-lock.json`.

### 5. Start the API

Open terminal 1 in the repository root:

```sh
. .venv/bin/activate
python -m uvicorn secure_cloud_platform.api:app \
  --host 127.0.0.1 \
  --port 8000
```

Leave this terminal running. Verify the API from another terminal:

```sh
curl --fail http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","simulation":true}
```

Useful API addresses:

| Address | Purpose |
| --- | --- |
| <http://127.0.0.1:8000/docs> | Interactive OpenAPI/Swagger interface |
| <http://127.0.0.1:8000/health> | Health check |
| <http://127.0.0.1:8000/version> | Application version |
| <http://127.0.0.1:8000/metrics> | Local text metrics |

### 6. Start the web portal

Open terminal 2 in the repository root:

```sh
cd web
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173> in a browser. The development server forwards API
requests to `127.0.0.1:8000`, so the API from the previous step must remain
running.

In the portal:

1. Open <http://127.0.0.1:5173/setup> and select AWS or Azure.
2. Keep **Simulation** selected for the executable local demo.
3. Activate the installation. The selected provider is then immutable.
4. Create an environment request from **New request**.
5. Review the normalized request, provider resources, and policy result.
6. Create a proposal and inspect its stable ID, content hash, and evidence.
7. Open **Operations** to see where protected deployment would begin.

Use AWS region `eu-west-1` or Azure region `northeurope` for the simplest demo.
The API keeps installation, request, proposal, and idempotency records in
process memory. Restarting the API clears the portal's local demo data.

### 7. Try the CLI

Open terminal 3 in the repository root and reactivate the Python environment:

```sh
. .venv/bin/activate
```

Create and validate an AWS simulation profile:

```sh
platform setup init \
  --provider aws \
  --mode simulation \
  --output profile.json

platform setup validate profile.json
platform setup status profile.json
```

Create a local example request:

```sh
cat > request.json <<'EOF'
{
  "application": "payments-api",
  "environment": "production",
  "owner": "Platform Team",
  "cost_centre": "FIN-042",
  "data_classification": "internal",
  "region": "eu-west-1",
  "network_cidr": "10.42.0.0/16",
  "cluster_size": "small",
  "monthly_budget": "250.00",
  "business_justification": "Credential-free portfolio demonstration",
  "non_production_expiry": null
}
EOF
```

Validate, render, and materialize its proposal:

```sh
platform request validate request.json --profile profile.json
platform request render request.json --profile profile.json
platform request propose request.json \
  --profile profile.json \
  --output proposal-bundle
```

The `proposal-bundle` directory contains the review evidence and generated
Terraform input values. These commands do not run Terraform or contact AWS.
To try Azure instead, create a separate profile with `--provider azure`, change
the request region to `northeurope`, and use a different output directory.

The CLI reconstructs its service from the supplied profile for each command.
It does not share the API process's in-memory records, so CLI-created requests
do not appear in the running portal.

### 8. Stop the services

Press `Ctrl-C` in the portal terminal and then in the API terminal. Activate
the virtual environment again with `. .venv/bin/activate` when returning to the
project later.

For a more detailed walkthrough, including policy-denial examples, see the
[local simulation quickstart](docs/simulation-quickstart.md) and
[portfolio demo](docs/portfolio-demo.md).

## Containers and Kubernetes packaging

The repository includes non-root, multi-stage Docker images for the API and
portal. Build them from the repository root:

```sh
docker build --file containers/api/Dockerfile \
  --tag secure-cloud-platform-api:local .

docker build --file containers/portal/Dockerfile \
  --tag secure-cloud-platform-portal:local .
```

Run the API container locally:

```sh
docker run --rm --publish 8000:8000 secure-cloud-platform-api:local
```

The portal image is a static production artifact intended to be wired to the
API by a deployment ingress or gateway. For a complete local portal demo, use
the source-based quick start above, where Vite supplies the API proxy.

The Helm chart can be rendered without contacting Kubernetes:

```sh
helm template platform deploy/helm/platform \
  --namespace secure-cloud-platform
```

The chart's default image repositories are placeholders. Rendering validates
the Kubernetes manifests; it does not deploy them. A real installation must
supply reviewed image references, ingress/gateway routing, workload identity,
and provider-specific protected configuration.

## Run the main checks

Python checks, from the repository root with the virtual environment active:

```sh
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

Portal checks:

```sh
cd web
npm run check
npm run build
```

Documentation checks require the pinned documentation dependencies:

```sh
python -m pip install --requirement requirements/docs.txt
python -m mkdocs build --strict
scripts/check-markdown-links.sh
scripts/check-repository-hygiene.sh
```

Terraform, policy, workflow, container, diagram, and full release-candidate
checks are described in the
[release-candidate checklist](docs/release-candidate-checklist.md).

## Architecture and security

The application uses one provider-neutral domain and policy layer with
explicit AWS and Azure adapters. FastAPI and Typer share the same application
service, while the React portal calls the API. Provider-specific Terraform
roots remain separate.

Real-capable plan, apply, drift, rollback, and two-stage destroy workflows are
inert by default. They require a private repository, manual dispatch from the
default branch, exact proposal and commit bindings, independent review,
protected GitHub Environments, concurrency controls, configured state, and
short-lived OIDC authentication.

Local validation must not contact AWS or Azure. Never commit credentials,
Terraform state, saved plans, private variable files, or real deployment
configuration.

## Documentation

Browse the
[published documentation website](https://abdalrahmanattya.github.io/secure-self-service-cloud-platform/)
or start with the [documentation index](docs/index.md) in the repository.
Important guides include:

- [Product overview](docs/product-overview.md)
- [Architecture tour](docs/architecture-tour.md)
- [Provider selection](docs/provider-selection.md)
- [Proposal lifecycle](docs/proposal-lifecycle.md)
- [AWS and Azure designs](docs/providers/README.md)
- [Portal, API, and CLI reference](docs/reference/README.md)
- [Security threat model](docs/security-threat-model.md)
- [Operations runbooks](docs/operations/README.md)
- [Architecture diagrams](docs/diagrams/README.md)
- [Architecture decisions](docs/decisions/README.md)

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change. Report
suspected vulnerabilities using the private process in [SECURITY.md](SECURITY.md),
not through a public issue.

## License

This project is available under the [MIT License](LICENSE).
