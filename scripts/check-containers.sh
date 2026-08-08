#!/bin/sh
set -eu

for dockerfile in containers/api/Dockerfile containers/portal/Dockerfile; do
  test -f "${dockerfile}"
  test "$(rg -c '^FROM ' "${dockerfile}")" -ge 2
  rg -q '^USER platform$' "${dockerfile}"
  if rg -n ':latest|COPY .*\.env|COPY .*secret' "${dockerfile}"; then
    echo "Container ${dockerfile} contains an unpinned or secret-bearing instruction." >&2
    exit 1
  fi
done

test -f deploy/helm/platform/Chart.yaml
test -f deploy/helm/platform/values.yaml
for template in api-deployment portal-deployment api-service portal-service serviceaccounts networkpolicy api-pdb portal-pdb; do
  test -f "deploy/helm/platform/templates/${template}.yaml"
done

rg -q 'runAsNonRoot: true' deploy/helm/platform/templates
rg -q 'readOnlyRootFilesystem: true' deploy/helm/platform/templates
rg -q 'allowPrivilegeEscalation: false' deploy/helm/platform/templates
rg -q 'capabilities:' deploy/helm/platform/templates
rg -q 'livenessProbe:' deploy/helm/platform/templates
rg -q 'readinessProbe:' deploy/helm/platform/templates
rg -q 'resources:' deploy/helm/platform/templates
rg -q 'podAntiAffinity:' deploy/helm/platform/templates
rg -q 'topologySpreadConstraints:' deploy/helm/platform/templates
rg -q 'kind: PodDisruptionBudget' deploy/helm/platform/templates
for pdb in api-pdb portal-pdb; do
  rg -q '^  unhealthyPodEvictionPolicy: AlwaysAllow$' "deploy/helm/platform/templates/${pdb}.yaml"
done
rg -q 'kind: NetworkPolicy' deploy/helm/platform/templates/networkpolicy.yaml
if rg -n 'kind: Secret|password:|client_secret|access_key' deploy/helm/platform; then
  echo "Helm chart must not embed secrets." >&2
  exit 1
fi

if command -v helm >/dev/null 2>&1; then
  helm lint deploy/helm/platform
  helm template example deploy/helm/platform >/dev/null
fi

if command -v kubeconform >/dev/null 2>&1; then
  helm template example deploy/helm/platform | kubeconform -strict -ignore-missing-schemas
fi
