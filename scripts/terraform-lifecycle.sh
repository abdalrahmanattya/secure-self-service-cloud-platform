#!/bin/sh
set -eu
: "${PROTECTED_OPERATION:?PROTECTED_OPERATION is required}"
: "${TF_PROVIDER:?TF_PROVIDER is required}"
: "${TF_MODE:?TF_MODE is required}"
: "${REQUEST_ID:?REQUEST_ID is required}"
: "${PROPOSAL_ID:?PROPOSAL_ID is required}"
: "${PROPOSAL_BUNDLE_DIR:?PROPOSAL_BUNDLE_DIR is required}"
: "${TFVARS_FILE:?TFVARS_FILE is required}"
: "${TFVARS_SHA256:?TFVARS_SHA256 is required}"
: "${PROPOSAL_FILE:?PROPOSAL_FILE is required}"
: "${PROPOSAL_SHA256:?PROPOSAL_SHA256 is required}"
printf '%s\n' "${TF_MODE}" | grep -Eq '^(sandbox|enterprise)$'

case "${TF_PROVIDER}" in
  aws) root="${GITHUB_WORKSPACE}/infrastructure/terraform/aws" ;;
  azure) root="${GITHUB_WORKSPACE}/infrastructure/terraform/azure" ;;
  *) exit 2 ;;
esac
scripts/validate-proposal-bundle.sh "${PROPOSAL_BUNDLE_DIR}" "${PROPOSAL_ID}"
expected_proposal_file="${PROPOSAL_BUNDLE_DIR}/environments/proposals/${PROPOSAL_ID}.json"
expected_tfvars_file="${PROPOSAL_BUNDLE_DIR}/infrastructure/terraform/${TF_PROVIDER}/${REQUEST_ID}.auto.tfvars.json"
test "${PROPOSAL_FILE}" = "${expected_proposal_file}"
test "${TFVARS_FILE}" = "${expected_tfvars_file}"
test -f "${TFVARS_FILE}"
echo "${TFVARS_SHA256}  ${TFVARS_FILE}" | sha256sum --check -
test -f "${PROPOSAL_FILE}"
echo "${PROPOSAL_SHA256}  ${PROPOSAL_FILE}" | sha256sum --check -
jq -e --arg provider "${TF_PROVIDER}" --arg mode "${TF_MODE}" --arg request "${REQUEST_ID}" --arg proposal "${PROPOSAL_ID}" '
  (keys | sort) == ["installation_id", "mode", "proposal_id", "provider", "request_fingerprint", "request_id", "schema_version", "state"] and
  .schema_version == "proposal.v1" and
  .proposal_id == $proposal and
  .request_id == $request and
  .provider == $provider and
  .mode == $mode and
  .state == "ready_for_review" and
  (.request_fingerprint | type == "string" and test("^[0-9a-f]{64}$")) and
  (.installation_id | type == "string" and length > 0)
' "${PROPOSAL_FILE}" >/dev/null
case "${TF_PROVIDER}" in
  aws) expected_tfvars_keys='["desired_nodes","mode","monthly_budget_usd","name_prefix","private_subnet_cidrs","public_subnet_cidrs","region","vpc_cidr"]' ;;
  azure) expected_tfvars_keys='["desired_nodes","location","mode","monthly_budget_eur","name_prefix","private_subnet_prefixes","vnet_address_space"]' ;;
esac
jq -e --argjson expected "${expected_tfvars_keys}" --arg mode "${TF_MODE}" '
  type == "object" and (keys | sort) == $expected and .mode == $mode
' "${TFVARS_FILE}" >/dev/null

if [ "${TF_PROVIDER}" = azure ]; then
  : "${TF_VAR_tenant_id:?TF_VAR_tenant_id is required for Azure}"
  : "${TF_VAR_subscription_id:?TF_VAR_subscription_id is required for Azure}"
  printf '%s\n' "${TF_VAR_tenant_id}" | grep -Eiq '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  printf '%s\n' "${TF_VAR_subscription_id}" | grep -Eiq '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  if printf '%s\n' "${TF_VAR_tenant_id}" | grep -Eiq '^0{8}-0{4}-0{4}-0{4}-0{12}$'; then exit 1; fi
  if printf '%s\n' "${TF_VAR_subscription_id}" | grep -Eiq '^0{8}-0{4}-0{4}-0{4}-0{12}$'; then exit 1; fi
fi

backend_file=$(mktemp)
trap 'rm -f "$backend_file"' EXIT HUP INT TERM
case "${TF_PROVIDER}" in
  aws)
    : "${TF_BACKEND_BUCKET:?TF_BACKEND_BUCKET is required}"
    : "${TF_BACKEND_REGION:?TF_BACKEND_REGION is required}"
    printf '%s\n' "${TF_BACKEND_BUCKET}" | grep -Eq '^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$'
    cat > "${backend_file}" <<EOF
bucket       = "${TF_BACKEND_BUCKET}"
key          = "platform/${REQUEST_ID}/${PROPOSAL_ID}.tfstate"
region       = "${TF_BACKEND_REGION}"
encrypt      = true
use_lockfile = true
EOF
    ;;
  azure)
    : "${TF_BACKEND_RESOURCE_GROUP:?TF_BACKEND_RESOURCE_GROUP is required}"
    : "${TF_BACKEND_STORAGE_ACCOUNT:?TF_BACKEND_STORAGE_ACCOUNT is required}"
    : "${TF_BACKEND_CONTAINER:?TF_BACKEND_CONTAINER is required}"
    printf '%s\n' "${TF_BACKEND_STORAGE_ACCOUNT}" | grep -Eq '^[a-z0-9]{3,24}$'
    cat > "${backend_file}" <<EOF
resource_group_name  = "${TF_BACKEND_RESOURCE_GROUP}"
storage_account_name = "${TF_BACKEND_STORAGE_ACCOUNT}"
container_name       = "${TF_BACKEND_CONTAINER}"
key                  = "platform/${REQUEST_ID}/${PROPOSAL_ID}.tfstate"
use_azuread_auth     = true
EOF
    ;;
esac

terraform -chdir="${root}" init -input=false -reconfigure -backend-config="${backend_file}"
case "${PROTECTED_OPERATION}" in
  plan) terraform -chdir="${root}" plan -input=false -out="${TF_PLAN_FILE}" -var-file="${TFVARS_FILE}" ;;
  apply|rollback) test -f "${TF_PLAN_FILE}"; terraform -chdir="${root}" apply -input=false "${TF_PLAN_FILE}" ;;
  drift) terraform -chdir="${root}" plan -input=false -detailed-exitcode -var-file="${TFVARS_FILE}" ;;
  destroy) terraform -chdir="${root}" plan -input=false -destroy -out="${TF_PLAN_FILE}" -var-file="${TFVARS_FILE}" ;;
  destroy-apply) test -f "${TF_PLAN_FILE}"; terraform -chdir="${root}" apply -input=false "${TF_PLAN_FILE}" ;;
esac
