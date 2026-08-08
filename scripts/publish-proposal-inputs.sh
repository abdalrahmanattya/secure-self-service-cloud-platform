#!/bin/sh
set -eu
: "${COMMIT_SHA:?COMMIT_SHA is required}"
: "${PROPOSAL_ID:?PROPOSAL_ID is required}"
printf '%s\n' "${COMMIT_SHA}" | grep -Eq '^[0-9a-fA-F]{40}$'
test "${COMMIT_SHA}" = "${GITHUB_SHA:-${COMMIT_SHA}}"
printf '%s\n' "${PROPOSAL_ID}" | grep -Eq '^proposal-[0-9a-f]{16}$'
source_dir="examples/proposals/${PROPOSAL_ID}"
scripts/validate-proposal-bundle.sh "${source_dir}" "${PROPOSAL_ID}"

proposal_file="${source_dir}/environments/proposals/${PROPOSAL_ID}.json"
provider=$(jq -er '.provider' "${proposal_file}")
request_id=$(jq -er '.request_id' "${proposal_file}")
tfvars_file="${source_dir}/infrastructure/terraform/${provider}/${request_id}.auto.tfvars.json"
output_dir=${OUTPUT_DIR:-.proposal-inputs}
test ! -e "${output_dir}"
mkdir -p "${output_dir}"
bundle_output="${output_dir}/bundle"
mkdir -p "${bundle_output}"
cp -R "${source_dir}/." "${bundle_output}/"
scripts/validate-proposal-bundle.sh "${bundle_output}" "${PROPOSAL_ID}"
proposal_output="${bundle_output}/environments/proposals/${PROPOSAL_ID}.json"
tfvars_output="${bundle_output}/infrastructure/terraform/${provider}/${request_id}.auto.tfvars.json"
sha256sum "${proposal_output}" > "${output_dir}/proposal.sha256"
sha256sum "${tfvars_output}" > "${output_dir}/tfvars.sha256"
