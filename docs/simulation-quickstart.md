# Local simulation quickstart

This quickstart runs the implemented simulation path locally: deterministic
AWS or Azure simulation adapters behind the shared service, a FastAPI API, the
Typer CLI, and the React portal. It creates no cloud resources and needs no
cloud credentials.

## Prerequisites

- Python 3.13
- Node.js and npm compatible with the pinned `web/package-lock.json`
- A shell with two or three terminal windows

The commands below assume the repository root is the current directory.

## Install the Python package

```sh
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --requirement requirements/dev.txt
```

The development requirements install the package in editable mode together
with the pinned API, CLI, test, lint, and type-check dependencies.

## Start the API

In the first terminal, from the repository root:

```sh
. .venv/bin/activate
python -m uvicorn secure_cloud_platform.api:app --host 127.0.0.1 --port 8000
```

The API is now available at <http://127.0.0.1:8000>. Check the local process
from a second terminal:

```sh
curl --fail http://127.0.0.1:8000/health
```

The response reports `"simulation":true`. The API stores its installation,
request, proposal, and idempotency records only in process memory; restarting
it clears that state.

## Start the web portal

In a second terminal, from the repository root:

```sh
cd web
npm ci
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>. Vite proxies API, health, version, and metrics
requests to `127.0.0.1:8000`. Use the setup page to select exactly one
provider. All modes can evaluate requests and create deterministic review
proposals locally. Simulation also returns mocked provider resources; sandbox
and enterprise are proposal-only and cannot perform cloud operations.

## Create and validate a CLI profile

In a terminal where the virtual environment is active, create an AWS
simulation profile:

```sh
platform setup init \
  --provider aws \
  --mode simulation \
  --output profile.json

platform setup validate profile.json
platform setup status profile.json
```

The profile is active, provider-locked, and defaults to the supported AWS
region `eu-west-1`. To exercise Azure instead, use
`--provider azure`; its default supported region is `northeurope`.

Create a request file with the following deterministic local example. This
example uses simulation mode so it also returns mocked provider resources:

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
  "business_justification": "Local deterministic simulation",
  "non_production_expiry": null
}
EOF

platform request validate request.json --profile profile.json
platform request render request.json --profile profile.json
platform request propose request.json --profile profile.json --output proposal-bundle
```

`validate` returns the normalized request, stable request ID, fingerprint, and
policy decision. `render` adds deterministic provider resource descriptions.
`propose` prints the immutable proposal and writes its seven artifacts plus a
`.platform-proposal.json` safety marker. The generated provider
`.auto.tfvars.json` is input evidence; no command runs Terraform or contacts a
provider. Change `environment` to `development` or `test` only when supplying a
future `non_production_expiry` date.

## What is and is not running

The local demo provides:

- immutable provider-neutral requests and policy decisions;
- deterministic AWS and Azure resource descriptions;
- one shared service used by API and CLI, plus a React client over the API;
- friendly provider and common-policy validation; and
- process-local API state with idempotent request/proposal handling; and
- deterministic proposal creation/status and safe CLI materialization.

It does not provide:

- AWS or Azure credentials, SDKs, account or subscription access;
- cloud API calls, cloud resources, remote state, or cloud cost;
- real Terraform plans, apply, drift, rollback, destroy, or bootstrap actions;
- durable proposal/API persistence; or
- configured GitHub Environments, repository variables, provider trust, state,
  accounts, or subscriptions.

AWS/Azure roots and protected workflows are implemented and locally validated,
but `REAL_DEPLOYMENT_ENABLED` remains absent or false and operator configuration
is not present. Sandbox and enterprise proposals use the same credential-free
evaluation path but do not execute provider resources locally. No live cloud
validation is implied. Stop the API and web
processes with `Ctrl-C` when finished.
