# Local simulation quickstart

This quickstart runs the implemented Milestones 3–5 path locally: deterministic
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

The response reports `"simulation":true`. The API stores its installation and
request records only in the process memory; restarting it clears that state.

## Start the web portal

In a second terminal, from the repository root:

```sh
cd web
npm ci
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173>. Vite proxies API, health, version, and metrics
requests to `127.0.0.1:8000`. Use the setup page to select exactly one
provider. The portal shows sandbox and enterprise as configuration-only modes;
simulation is the only executable mode in this demo.

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

Create a request file with the following deterministic, simulation-only
example:

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
```

`validate` returns the normalized request, stable request ID, fingerprint, and
policy decision. `render` includes the same decision plus the deterministic
provider resource descriptions. Neither command writes Terraform, calls a
provider, or applies infrastructure. Change `environment` to `development` or
`test` only when supplying a future `non_production_expiry` date.

## What is and is not running

The local demo provides:

- immutable provider-neutral requests and policy decisions;
- deterministic AWS and Azure resource descriptions;
- one shared service used by API and CLI, plus a React client over the API;
- friendly provider and common-policy validation; and
- process-local API state with idempotent request handling.

It does not provide:

- AWS or Azure credentials, SDKs, account or subscription access;
- cloud API calls, cloud resources, remote state, or cloud cost;
- Terraform modules, proposals, plans, apply, destroy, or rollback actions; or
- executable sandbox or enterprise deployment configuration.

Sandbox and enterprise are intentionally configuration-only descriptions for
future protected delivery. Stop the API and web processes with `Ctrl-C` when
finished.
