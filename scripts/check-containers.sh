#!/bin/sh
set -eu

for dockerfile in containers/api/Dockerfile containers/portal/Dockerfile; do
  test -f "${dockerfile}"
  test "$(grep -Ec '^FROM ' "${dockerfile}")" -ge 2
  grep -Eq '^USER platform$' "${dockerfile}"
  if grep -En ':latest|COPY .*\.env|COPY .*secret' "${dockerfile}"; then
    echo "Container ${dockerfile} contains an unpinned or secret-bearing instruction." >&2
    exit 1
  fi
done

test -f deploy/helm/platform/Chart.yaml
test -f deploy/helm/platform/values.yaml
for template in api-deployment portal-deployment api-service portal-service serviceaccounts networkpolicy api-pdb portal-pdb; do
  test -f "deploy/helm/platform/templates/${template}.yaml"
done

grep -Eqr 'runAsNonRoot: true' deploy/helm/platform/templates
grep -Eqr 'readOnlyRootFilesystem: true' deploy/helm/platform/templates
grep -Eqr 'allowPrivilegeEscalation: false' deploy/helm/platform/templates
grep -Eqr 'capabilities:' deploy/helm/platform/templates
grep -Eqr 'livenessProbe:' deploy/helm/platform/templates
grep -Eqr 'readinessProbe:' deploy/helm/platform/templates
grep -Eqr 'resources:' deploy/helm/platform/templates
grep -Eqr 'podAntiAffinity:' deploy/helm/platform/templates
grep -Eqr 'topologySpreadConstraints:' deploy/helm/platform/templates
grep -Eqr 'kind: PodDisruptionBudget' deploy/helm/platform/templates
for pdb in api-pdb portal-pdb; do
  grep -Eq '^  unhealthyPodEvictionPolicy: AlwaysAllow$' "deploy/helm/platform/templates/${pdb}.yaml"
done
grep -Eq 'kind: NetworkPolicy' deploy/helm/platform/templates/networkpolicy.yaml
if grep -Enr 'kind: Secret|password:|client_secret|access_key' deploy/helm/platform; then
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
