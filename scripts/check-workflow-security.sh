#!/bin/sh
set -eu

workflow_dir=.github/workflows

awk '/uses:/ { split($0, parts, "@"); if (length(parts) != 2 || parts[2] !~ /^[0-9a-f]{40}([[:space:]]|#|$)/) { print; bad=1 } } END { exit bad }' "${workflow_dir}"/*.yml

for workflow in proposal-validation deploy-plan deploy-apply deploy-rollback deploy-drift deploy-destroy deploy-destroy-apply; do
  file="${workflow_dir}/${workflow}.yml"
  test -f "${file}"
  if [ "${workflow}" != proposal-validation ]; then
    rg -q "vars\.REAL_DEPLOYMENT_ENABLED == 'true'" "${file}"
    rg -q 'github\.event\.repository\.private == true' "${file}"
    rg -q '^concurrency:' "${file}"
    rg -q 'id-token: write' "${file}"
    rg -q 'environment:' "${file}"
    rg -q 'reviewer' "${file}"
    rg -q 'requester' "${file}"
    rg -q 'reviewer.*requester|requester.*reviewer' "${file}"
    rg -q 'PROPOSAL_BUNDLE_DIR:' "${file}"
    rg -q 'environments/proposals/\$\{\{ inputs\.proposal_id \}\}\.json' "${file}"
    rg -q 'infrastructure/terraform/\$\{\{ inputs\.provider \}\}/\$\{\{ inputs\.request_id \}\}\.auto\.tfvars\.json' "${file}"
    rg -q 'TF_VAR_tenant_id: \$\{\{ vars\.AZURE_TENANT_ID \}\}' "${file}"
    rg -q 'TF_VAR_subscription_id: \$\{\{ vars\.AZURE_SUBSCRIPTION_ID \}\}' "${file}"
  fi
  rg -q '^permissions:' "${file}"
  if [ "${workflow}" != proposal-validation ] && rg -q '^  (push|pull_request):' "${file}"; then
    echo "Protected lifecycle workflow ${file} cannot run on push or pull_request." >&2
    exit 1
  fi
done

rg -q 'retention-days: 1' .github/workflows/deploy-plan.yml
rg -q 'retention-days: 1' .github/workflows/deploy-destroy.yml
rg -q 'plans can contain sensitive values' .github/workflows/deploy-plan.yml

if rg -n 'run:.*\$\{\{.*inputs\.' "${workflow_dir}"; then
  echo "Untrusted workflow inputs must be passed through environment variables, not shell interpolation." >&2
  exit 1
fi

if rg -n 'terraform (apply|plan|init)' "${workflow_dir}"/deploy-*.yml; then
  echo "Protected workflows must invoke the verified lifecycle wrapper for selected-root execution." >&2
  exit 1
fi

if rg -n '/\.protected-(inputs|plan)/(proposal\.json|terraform\.tfvars\.json)' "${workflow_dir}"/deploy-*.yml; then
  echo "Lifecycle workflows must consume the nested materialized proposal bundle." >&2
  exit 1
fi

for workflow in deploy-plan deploy-apply deploy-rollback deploy-drift deploy-destroy deploy-destroy-apply; do
  file="${workflow_dir}/${workflow}.yml"
  rg -q 'scripts/install-terraform.sh' "${file}"
  rg -q 'scripts/authenticate-oidc.sh' "${file}"
  rg -q 'scripts/terraform-lifecycle.sh' "${file}"
  rg -q 'TF_BACKEND_' "${file}"
done

rg -q 'name: destroy-plan-\$\{\{ inputs.proposal_id \}\}' .github/workflows/deploy-destroy.yml
rg -q 'name: destroy-plan-\$\{\{ inputs.proposal_id \}\}' .github/workflows/deploy-destroy-apply.yml
if rg -n 'rollback-\$\{\{ inputs.proposal_id \}\}' .github/workflows; then
  echo "Rollback must consume the reviewed plan artifact produced by the plan workflow." >&2
  exit 1
fi

if rg -n 'options: \[simulation, sandbox, enterprise\]' .github/workflows/deploy-*.yml; then
  echo "Protected cloud workflows must not offer simulation mode." >&2
  exit 1
fi

if rg -n 'aquasecurity/trivy-action|setup-trivy' .github/workflows; then
  echo "The compromised Trivy action integration is prohibited." >&2
  exit 1
fi

if rg -n 'AWS_'"ACCESS_KEY_ID"'|AWS_'"SECRET_ACCESS_KEY"'|AZURE_'"CLIENT_SECRET"'|ARM_'"CLIENT_SECRET"'|BEGIN (RSA|OPENSSH|EC)' .github/workflows infrastructure deploy containers; then
  echo "Static credentials or private keys are prohibited." >&2
  exit 1
fi
