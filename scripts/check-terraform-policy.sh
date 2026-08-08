#!/bin/sh
set -eu

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to inspect Terraform's JSON version output." >&2
  exit 127
fi
terraform_version_json=$(terraform version -json)
terraform_version=$(printf '%s\n' "${terraform_version_json}" | jq -er '
  if type != "object" or (.terraform_version | type) != "string" then
    error("Terraform version JSON has no string terraform_version field")
  else
    .terraform_version
  end
')
test "${terraform_version}" = '1.15.8'

terraform fmt -check -recursive infrastructure/terraform infrastructure/terraform/aws-bootstrap infrastructure/terraform/azure-bootstrap

for root in infrastructure/terraform/aws infrastructure/terraform/aws-bootstrap infrastructure/terraform/azure infrastructure/terraform/azure-bootstrap; do
  terraform -chdir="${root}" init -backend=false -input=false -upgrade=false
  terraform -chdir="${root}" validate
  terraform -chdir="${root}" test -no-color
done

conftest_bin=${CONFTEST_BIN:-conftest}
if ! command -v "${conftest_bin}" >/dev/null 2>&1 && [ ! -x "${conftest_bin}" ]; then
  echo "Conftest v0.69.0 is required; install it with scripts/install-conftest.sh." >&2
  exit 127
fi

if ! "${conftest_bin}" --version | grep -q 'Conftest: 0.69.0'; then
  echo "Conftest 0.69.0 is required." >&2
  exit 1
fi

"${conftest_bin}" test --all-namespaces --strict --policy policy examples/policy/pass-aws-sandbox.json examples/policy/pass-azure-sandbox.json
if "${conftest_bin}" test --all-namespaces --strict --policy policy examples/policy/fail-sandbox-production.json; then
  echo "The deliberately failing policy fixture unexpectedly passed." >&2
  exit 1
fi
