#!/bin/sh
set -eu

workflow_dir=.github/workflows

awk '/uses:/ { split($0, parts, "@"); if (length(parts) != 2 || parts[2] !~ /^[0-9a-f]{40}([[:space:]]|#|$)/) { print; bad=1 } } END { exit bad }' "${workflow_dir}"/*.yml

for workflow in proposal-validation deploy-plan deploy-apply deploy-rollback deploy-drift deploy-destroy deploy-destroy-apply; do
  file="${workflow_dir}/${workflow}.yml"
  test -f "${file}"
  if [ "${workflow}" != proposal-validation ]; then
    grep -Eq "vars\.REAL_DEPLOYMENT_ENABLED == 'true'" "${file}"
    grep -Eq 'github\.event\.repository\.private == true' "${file}"
    grep -Eq '^concurrency:' "${file}"
    grep -Eq 'id-token: write' "${file}"
    grep -Eq 'environment:' "${file}"
    grep -Eq 'reviewer' "${file}"
    grep -Eq 'requester' "${file}"
    grep -Eq 'reviewer.*requester|requester.*reviewer' "${file}"
    grep -Eq 'PROPOSAL_BUNDLE_DIR:' "${file}"
    grep -Eq 'environments/proposals/\$\{\{ inputs\.proposal_id \}\}\.json' "${file}"
    grep -Eq 'infrastructure/terraform/\$\{\{ inputs\.provider \}\}/\$\{\{ inputs\.request_id \}\}\.auto\.tfvars\.json' "${file}"
    grep -Eq 'TF_VAR_tenant_id: \$\{\{ vars\.AZURE_TENANT_ID \}\}' "${file}"
    grep -Eq 'TF_VAR_subscription_id: \$\{\{ vars\.AZURE_SUBSCRIPTION_ID \}\}' "${file}"
  fi
  grep -Eq '^permissions:' "${file}"
  if [ "${workflow}" != proposal-validation ] && grep -Eq '^  (push|pull_request):' "${file}"; then
    echo "Protected lifecycle workflow ${file} cannot run on push or pull_request." >&2
    exit 1
  fi
done

grep -Eq 'retention-days: 1' .github/workflows/deploy-plan.yml
grep -Eq 'retention-days: 1' .github/workflows/deploy-destroy.yml
grep -Eq 'plans can contain sensitive values' .github/workflows/deploy-plan.yml

if git grep -En 'run:.*\$\{\{.*inputs\.' -- "${workflow_dir}"; then
  echo "Untrusted workflow inputs must be passed through environment variables, not shell interpolation." >&2
  exit 1
fi

if grep -En 'terraform (apply|plan|init)' "${workflow_dir}"/deploy-*.yml; then
  echo "Protected workflows must invoke the verified lifecycle wrapper for selected-root execution." >&2
  exit 1
fi

if grep -En '/\.protected-(inputs|plan)/(proposal\.json|terraform\.tfvars\.json)' "${workflow_dir}"/deploy-*.yml; then
  echo "Lifecycle workflows must consume the nested materialized proposal bundle." >&2
  exit 1
fi

for workflow in deploy-plan deploy-apply deploy-rollback deploy-drift deploy-destroy deploy-destroy-apply; do
  file="${workflow_dir}/${workflow}.yml"
  grep -Eq 'scripts/install-terraform.sh' "${file}"
  grep -Eq 'scripts/authenticate-oidc.sh' "${file}"
  grep -Eq 'scripts/terraform-lifecycle.sh' "${file}"
  grep -Eq 'TF_BACKEND_' "${file}"
done

grep -Eq 'name: destroy-plan-\$\{\{ inputs.proposal_id \}\}' .github/workflows/deploy-destroy.yml
grep -Eq 'name: destroy-plan-\$\{\{ inputs.proposal_id \}\}' .github/workflows/deploy-destroy-apply.yml
if git grep -En 'rollback-\$\{\{ inputs.proposal_id \}\}' -- .github/workflows; then
  echo "Rollback must consume the reviewed plan artifact produced by the plan workflow." >&2
  exit 1
fi

if grep -En 'options: \[simulation, sandbox, enterprise\]' .github/workflows/deploy-*.yml; then
  echo "Protected cloud workflows must not offer simulation mode." >&2
  exit 1
fi

if git grep -En 'aquasecurity/trivy-action|setup-trivy' -- .github/workflows; then
  echo "The compromised Trivy action integration is prohibited." >&2
  exit 1
fi

if git grep -En 'AWS_'"ACCESS_KEY_ID"'|AWS_'"SECRET_ACCESS_KEY"'|AZURE_'"CLIENT_SECRET"'|ARM_'"CLIENT_SECRET"'|BEGIN (RSA|OPENSSH|EC)' -- .github/workflows infrastructure deploy containers; then
  echo "Static credentials or private keys are prohibited." >&2
  exit 1
fi
