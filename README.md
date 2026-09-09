<!-- reader-first-readme:v1 -->

# Secure Self-Service Cloud Platform

[![Quality](https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/actions/workflows/quality.yml/badge.svg)](https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/actions/workflows/quality.yml)
[![Documentation](https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/actions/workflows/pages.yml/badge.svg)](https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/actions/workflows/pages.yml)
[![Latest release](https://img.shields.io/github/v/release/abdalrahmanattya/secure-self-service-cloud-platform)](https://github.com/abdalrahmanattya/secure-self-service-cloud-platform/releases/latest)
[![MIT license](https://img.shields.io/github/license/abdalrahmanattya/secure-self-service-cloud-platform)](LICENSE)

An internal developer platform for requesting secure,
policy-compliant Kubernetes environments on either Amazon Web Services (AWS)
or Microsoft Azure.

An administrator selects one provider and one operating mode. Developers then
use a friendly portal, REST API, or CLI to submit requests. The platform
normalizes each request, evaluates policy, describes the expected provider
resources, and creates a deterministic proposal for review.

## The short version

1. An administrator chooses AWS or Azure for one installation and defines its
   safety rules.
2. A developer describes the environment an application needs without having
   to design the cloud network or Kubernetes cluster.
3. The platform checks ownership, cost, location, networking, data protection,
   logging, and expiry requirements.
4. An unsafe request is rejected with specific guidance; an accepted request
   becomes a repeatable proposal with stable identifiers and hashes.
5. A reviewer can inspect exactly what would be created before any cloud access
   is granted.
6. Only a separately configured, protected GitHub workflow can turn an approved
   proposal into a cloud plan or deployment.

## A representative developer journey

Imagine a product team needs a temporary test environment. A developer opens
the portal, selects the application owner, region, network range, monthly
budget, expiry date, and required data protection. The platform checks the
request against the organization's rules.

If the request asks for a public Kubernetes cluster or exceeds the allowed
budget, the developer sees which fields must change. Once it passes, the same
request produces the same review bundle whether it came from the portal, API,
or command line. A platform administrator can then carry that bundle into a
private review process. The portal itself cannot create or delete cloud
resources.

## Why it is useful

Development teams often wait for specialist help or copy old infrastructure
when they need a new environment. This platform turns that request into a
consistent conversation: developers describe the outcome, policies catch
unsafe or unaffordable choices early, and administrators receive a stable,
reviewable proposal rather than an undocumented cloud change.

## Portal preview

The responsive portal is a dark-sidebar control-plane experience for a
provider-locked installation. On smaller screens the sidebar becomes a mobile
drawer. API-derived metrics, guided request/policy/proposal flows, readiness and
operations views, and accessible evidence and copy controls keep the review
path clear. It has no direct cloud lifecycle controls; protected external
workflows own any eventual execution.

![Secure Self-Service Cloud Platform portal dashboard](docs/images/portal-dashboard.jpg)

### Animated walkthroughs

These short recordings use credential-free simulation data. They create no
cloud resources, make no cloud API calls, and do not run Terraform or apply
infrastructure.

#### 1. Provider and mode installation setup

[![Portal setup walkthrough: choose a provider and simulation mode](docs/images/portal-setup.gif)](docs/reference/portal.md#setup)

#### 2. Environment request and policy review

[![Portal request review walkthrough: submit a request and inspect the policy decision](docs/images/portal-request-review.gif)](docs/reference/portal.md#request-review)

#### 3. Proposal evidence, readiness, and guarded operations

[![Portal proposal readiness walkthrough: inspect deterministic evidence and review status](docs/images/portal-proposal-readiness.gif)](docs/reference/portal.md#deployment-proposal)

Read the [authoritative portal reference](docs/reference/portal.md) for the
complete workflow and its safety boundaries.

## System architecture diagram: how a request moves

![Secure Self-Service Cloud Platform system context](docs/diagrams/rendered/system-context.svg)

In plain language, developers and administrators use the platform to create a
checked proposal. All three interfaces share the same rules and provider
selection. The proposal crosses into GitHub only through an operator-controlled
handoff. A protected workflow may then target either AWS or Azure—but never both
from the same installation—and only after separate configuration and approval.

## Key capabilities

- One provider-locked installation for AWS or Azure; this is not a hybrid-cloud
  deployment system.
- Simulation, sandbox, and enterprise operating modes with different safety
  boundaries.
- One domain model shared by the React portal, FastAPI API, and Typer CLI.
- Friendly policy feedback for ownership, cost, network, data classification,
  encryption, private Kubernetes, logging, expiry, and production controls.
- Deterministic request IDs, fingerprints, resource descriptions, proposal
  hashes, and review artifacts.
- Separate AWS and Azure Terraform roots with provider-native network,
  Kubernetes, identity, logging, encryption, state, and budget designs.
- Protected GitHub workflow designs for proposal review, plan, apply, drift,
  rollback, and destroy. Direct `terraform apply` is not exposed through the
  portal, API, or CLI.

## Who uses it

- Platform administrators select the provider and mode, configure guardrails,
  and approve protected workflows.
- Developers request standard environments without needing to design all cloud
  infrastructure themselves.
- Security teams review policy, identity, encryption, and audit boundaries.
- Operations teams own monitoring, drift, incident response, rollback, and
  recovery.
- Finance teams define budgets, expiry, and cost attribution requirements.

## Choose your path

| Goal | Start here | What to expect |
| --- | --- | --- |
| Evaluate the design | [Published documentation](https://abdalrahmanattya.github.io/secure-self-service-cloud-platform/) and [architecture tour](docs/architecture-tour.md) | Review the product, interfaces, security model, and provider diagrams. |
| Run the local demo | [Local quick start](#local-quick-start) and [simulation guide](docs/simulation-quickstart.md) | Use mocked providers with no credentials, cloud calls, resources, or cost. |
| Prepare a real deployment | [Administrator deployment guide](docs/administrator-deployment-guide.md) | Supply private AWS/Azure and GitHub values, publish your own images, configure identity and state, and complete acceptance testing. |
| Contribute | [Contributing guide](CONTRIBUTING.md) | Run the relevant checks, explain the change, and keep public documentation accurate. |

## Technology guide in plain English

| Technology | Its job in this product |
| --- | --- |
| React | Builds the visual portal used to configure an installation and review requests. |
| FastAPI | Provides the web API used by the portal and other integrations. |
| Typer | Provides the command-line interface for operators who prefer terminal workflows. |
| Open Policy Agent and Rego | Evaluate requests against written safety and governance rules. Rego is the language used to express those rules. |
| Terraform | Describes the expected AWS or Azure infrastructure as reviewable configuration. |
| GitHub Actions | Provides the protected review, plan, approval, deployment, drift, rollback, and removal workflow boundary. |
| OpenID Connect (OIDC) | Lets an approved workflow obtain short-lived cloud access without storing permanent cloud keys in GitHub. |
| Docker and Helm | Package the portal and API as containers and describe how they would run on Kubernetes. |
| Kubernetes | Runs containerized applications across a managed cluster; Amazon EKS and Azure AKS are the provider-managed versions. |

## Local quick start

The executable demonstration uses the API and portal from source. It requires
Python 3.13, Node.js 22 with npm, Git, and `curl`; it does not require AWS or
Azure credentials.

```sh
git clone https://github.com/abdalrahmanattya/secure-self-service-cloud-platform.git
cd secure-self-service-cloud-platform
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install --requirement requirements/dev.txt
cd web && npm ci && cd ..
```

Start the API in terminal 1:

```sh
. .venv/bin/activate
python -m uvicorn secure_cloud_platform.api:app --host 127.0.0.1 --port 8000
```

Check <http://127.0.0.1:8000/health>, then start the portal in terminal 2:

```sh
cd web
npm run dev -- --host 127.0.0.1
```

Open <http://127.0.0.1:5173/setup> and follow this walkthrough:

1. Choose **AWS** or **Azure**, then choose **Simulation**. The provider is
   locked when you select **Create installation**; AWS and Azure are separate
   installation choices, not a hybrid setup.
2. On **Environment dashboard**, confirm the installation context and
   API-derived **Requests**, **Accepted requests**, **Review proposals**, and
   **Cloud changes** metrics. The last metric remains `0` because the portal
   does not execute cloud changes.
3. Select **New request**. Complete the grouped **Ownership**, **Environment
   intent**, **Infrastructure**, and **Governance** inputs. The region is
   prefilled from the installation's allowed-region default, and the **Request
   summary** updates live with application, environment, region, budget, and
   installation context.
4. Select **Review request**. An accepted request shows **Request accepted**,
   evaluated provider resources, and **Create review proposal**. A denied
   request shows **Request denied** with field-level policy feedback and no
   proposal button. Return to **New request**, correct the inputs, and submit
   again.
5. For an accepted request, select **Create review proposal**. In the
   proposal-evidence view headed **Deployment proposal**, inspect the **Ready
   for review** status, linked request, IDs, content hash, fingerprint, and
   deterministic artifact accordions. The first artifact is expanded initially;
   the others can be expanded. Use the copy controls for IDs and hashes; copy
   success or failure is announced accessibly.
6. Open **Readiness** to distinguish available credential-free capabilities
   from **Guarded** administrator-owned prerequisites. Open **Operations** to
   review proposal evidence and the guarded lifecycle: GitHub review, protected
   plan, approval, apply, and drift/rollback/destroy stages are described as
   not executed.
7. The API keeps installation, request, proposal, and idempotency state in
   process memory. Restarting the API resets the local demo. Any protected
   external workflow is a separate operator-controlled hand-off; the portal,
   API, and CLI do not apply infrastructure or claim that cloud execution ran.

For the complete walkthrough, including policy-denial examples and Azure,
read the [simulation quickstart](docs/simulation-quickstart.md).

### Short CLI example

First create `request.json` using the full example in the [simulation
guide](docs/simulation-quickstart.md), then run the commands below.

```sh
. .venv/bin/activate
platform setup init --provider aws --mode simulation --output profile.json
platform setup validate profile.json
platform request validate request.json --profile profile.json
platform request render request.json --profile profile.json
platform request propose request.json --profile profile.json --output proposal-bundle
```

CLI proposal generation is local and deterministic; it does not run Terraform
or contact AWS or Azure.

## Exact deployment method for AWS or Azure

The platform supports AWS and Azure as alternative installation targets. An
installation chooses exactly one provider; managing both means two separate
installations, deployment repositories, identities, state backends, and
operating boundaries.

The public repository contains the application, separate provider modules,
policy, workflow definitions, and expected-resource designs. An administrator
must provide private account or subscription values, network and identity
configuration, protected GitHub settings, durable state, runtime image
references, ingress, DNS, TLS, secrets, and operational controls.

Read the [administrator deployment guide](docs/administrator-deployment-guide.md)
before planning a real installation. It explains responsibilities, stop
conditions, sandbox versus enterprise expectations, and the private deployment
repository model.

### AWS expected deployment design

![Expected AWS installation path from protected review through identity, state, network, Kubernetes, encryption, audit, monitoring, and budget services](docs/images/aws-cloud-architecture.png)

An approved workflow receives short-lived access through AWS Identity and
Access Management (IAM). Terraform state is protected in Amazon S3, while the
environment design places a private Amazon EKS cluster inside an Amazon VPC.
AWS KMS protects sensitive data, CloudTrail and CloudWatch provide evidence,
and AWS Budgets sets a monthly cost boundary.

### Azure expected deployment design

![Expected Azure installation path from protected review through identity, state, network, Kubernetes, secrets, monitoring, and budget services](docs/images/azure-cloud-architecture.png)

The Azure alternative follows the same control pattern with provider-native
services: federated managed identities, a protected Storage Account, a Virtual
Network, private Azure Kubernetes Service, Key Vault, Log Analytics, and an
Azure budget.

Both diagrams describe deployable designs represented by the Terraform roots,
not currently running shared environments. The release's code and local
simulation were validated, but no real AWS or Azure installation has been
executed. An operator who wants a live installation must supply private values,
build runtime images, configure protected workflows, and complete sandbox
acceptance in their own account or subscription.

The expected/planned provider resources in these diagrams were not deployed as
part of release validation; the exact guarded path is documented in the
[administrator deployment guide](docs/administrator-deployment-guide.md).

The diagrams use the [official AWS Architecture Icons](https://aws.amazon.com/architecture/icons/),
the [official Microsoft Azure Architecture Icons](https://learn.microsoft.com/azure/architecture/icons/),
and the official GitHub mark. More detailed expected-resource, topology, trust,
sequence, and state views remain in the [complete diagram catalogue](docs/diagrams/README.md).

## Important limitations

- The local application keeps installation, request, proposal, and retry state
  in memory; restarting it clears the demonstration data.
- The portal and API do not include production user authentication or
  role-based authorization.
- Runtime container images are not published, and organization-specific DNS,
  TLS, secrets, ingress, identity, storage, backup, and recovery are not
  configured by this public repository.
- Terraform and policy tests cannot prove provider quotas, live identity,
  network reachability, long-term reliability, performance, or cost.
- AWS and Azure are alternatives. Supporting both requires two independent
  installations and operating boundaries.

## Production-readiness and security boundary

The release is designed to be extended into a protected deployment, but it is
not a turnkey managed service or live-cloud-certified distribution. Before a
real installation, an administrator must at minimum:

- use a private deployment repository and protected GitHub Environments;
- establish provider state, OIDC trust, roles/identities, and least-privilege
  access;
- build and publish reviewed immutable API and portal images;
- connect the portal and API through an ingress or gateway with TLS;
- add durable application storage, backup, retention, and recovery;
- integrate organizational authentication, authorization, and audit controls;
- verify monitoring, alerting, budgets, drift, rollback, and destroy paths; and
- complete provider-specific sandbox acceptance before enterprise use.

The included workflows fail closed by default and require exact proposal and
commit bindings, manual dispatch, approval, concurrency controls, and
short-lived OIDC credentials. Do not commit credentials, Terraform state,
saved plans, private variable files, or real account/subscription values.

## Containers and Kubernetes packaging

The repository includes non-root, multi-stage Dockerfiles and a Helm chart for
the API and portal. Build locally with:

```sh
docker build --file containers/api/Dockerfile --tag secure-cloud-platform-api:local .
docker build --file containers/portal/Dockerfile --tag secure-cloud-platform-portal:local .
helm template platform deploy/helm/platform --namespace secure-cloud-platform
```

The portal image is a static artifact and needs deployment ingress or gateway
routing to the API. The chart uses placeholder image repositories. No runtime
images are published by this repository.

## What was tested

With the Python virtual environment active:

```sh
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy
```

For the portal and public documentation:

```sh
cd web && npm run check && npm run build && cd ..
python -m pip install --requirement requirements/docs.txt
python -m mkdocs build --strict
scripts/check-markdown-links.sh
scripts/check-repository-hygiene.sh
```

The [release checklist](docs/release-candidate-checklist.md) describes the
broader Terraform, policy, workflow, container, Helm, diagram, and acceptance
checks.

## Documentation

- [Published documentation](https://abdalrahmanattya.github.io/secure-self-service-cloud-platform/)
- [Product overview](docs/product-overview.md)
- [Administrator deployment guide](docs/administrator-deployment-guide.md)
- [AWS and Azure provider designs](docs/providers/README.md)
- [Portal, API, and CLI reference](docs/reference/README.md)
- [Security threat model](docs/security-threat-model.md)
- [Operations runbooks](docs/operations/README.md)
- [Architecture diagrams](docs/diagrams/README.md)
- [Architecture decisions](docs/decisions/README.md)

## Repository map

| Location | Contents |
| --- | --- |
| `src/secure_cloud_platform` | Shared request model, policies, provider adapters, API, CLI, and proposal service. |
| `web` | React portal and generated API client. |
| `policy` | Common, AWS, and Azure policy rules. |
| `infrastructure/terraform` | Separate bootstrap and environment roots for AWS and Azure. |
| `deploy/helm` and `containers` | Kubernetes packaging and container definitions. |
| `.github/workflows` | Quality checks and protected lifecycle workflow designs. |
| `docs` | Architecture, security, operations, provider, and interface documentation. |
| `tests` and `examples` | Automated behavior checks and fictional request/proposal examples. |

## Contributing, security, and license

See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change. Report
suspected vulnerabilities using the private process in [SECURITY.md](SECURITY.md),
not through a public issue.

This project is available under the [MIT License](LICENSE).
