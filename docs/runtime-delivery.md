# Runtime containers and Helm

The API and portal have separate multi-stage container definitions and one Helm
application chart under `deploy/helm/platform`. They are implemented and their
security contracts are locally checked; no image or chart is published by this
release.

See the
[administrator deployment guide](administrator-deployment-guide.md) before
using these artifacts. A running chart is only one part of a real installation
and does not provide production authentication, persistence, routing, secrets,
or operational integration by itself.

## Containers

- API: Python `3.13.7` builder/runtime, local wheel installation, UID/GID
  `10001`, non-root Uvicorn on port `8000`.
- Portal: Node `22.14.0` build, nginx `1.29.1` runtime, UID/GID `10001`,
  non-root HTTP on port `8080`.
- Both use exact base tags, no `latest`, no copied secret files, and explicit
  runtime users. Digest promotion remains a release-hardening follow-up.

## Helm chart

The chart deploys two replicas each by default with Services, dedicated service
accounts, liveness/readiness probes, resource requests/limits, runtime-default
seccomp, non-root IDs, read-only root filesystems, dropped capabilities,
anti-affinity, topology spread, and PodDisruptionBudgets.

NetworkPolicy defaults to deny and permits only ingress-controller-to-portal,
portal-to-API, and DNS paths. Service-account token automount is disabled. The
chart deliberately renders no Secret or ExternalSecret; an operator-reviewed
overlay must supply provider-native workload identity and external secrets.

The release values use sanitized GHCR example names and `1.0.0`; they do not
refer to published images.
