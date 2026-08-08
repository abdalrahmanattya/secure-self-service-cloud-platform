#!/bin/sh
set -eu

proposal_id=proposal-0123456789abcdef
bundle_dir="examples/proposals/${proposal_id}"
scripts/validate-proposal-bundle.sh "${bundle_dir}" "${proposal_id}"

work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM
commit_sha=$(git rev-parse HEAD)
COMMIT_SHA="${commit_sha}" GITHUB_SHA="${commit_sha}" PROPOSAL_ID="${proposal_id}" \
  OUTPUT_DIR="${work_dir}/published" scripts/publish-proposal-inputs.sh
sha256sum --check "${work_dir}/published/proposal.sha256"
sha256sum --check "${work_dir}/published/tfvars.sha256"

cp -R "${bundle_dir}" "${work_dir}/extra-key"
tfvars_file="${work_dir}/extra-key/infrastructure/terraform/aws/env-0123456789abcdef.auto.tfvars.json"
jq '. + {request_id: "env-0123456789abcdef"}' "${tfvars_file}" > "${work_dir}/mutated.json"
mv "${work_dir}/mutated.json" "${tfvars_file}"
if scripts/validate-proposal-bundle.sh "${work_dir}/extra-key" "${proposal_id}"; then
  echo "A proposal tfvars file with a non-contract metadata key was accepted." >&2
  exit 1
fi

cp -R "${bundle_dir}" "${work_dir}/missing-path"
rm "${work_dir}/missing-path/environments/policies/env-0123456789abcdef.md"
if scripts/validate-proposal-bundle.sh "${work_dir}/missing-path" "${proposal_id}"; then
  echo "A proposal bundle inconsistent with its marker was accepted." >&2
  exit 1
fi
