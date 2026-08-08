#!/bin/sh
set -eu

: "${1:?proposal bundle directory is required}"
: "${2:?proposal ID is required}"
bundle_dir=$1
proposal_id=$2

printf '%s\n' "${proposal_id}" | grep -Eq '^proposal-[0-9a-f]{16}$'
test -d "${bundle_dir}"
test ! -L "${bundle_dir}"
if find "${bundle_dir}" -type l | grep -q .; then
  echo "Proposal bundles must not contain symbolic links." >&2
  exit 1
fi

marker_file="${bundle_dir}/.platform-proposal.json"
test -f "${marker_file}"
jq -e --arg proposal "${proposal_id}" '
  (keys | sort) == ["artifact_paths", "content_hash", "proposal_id", "schema_version"] and
  .schema_version == "proposal.v1" and
  .proposal_id == $proposal and
  (.content_hash | type == "string" and test("^[0-9a-f]{64}$")) and
  (.artifact_paths | type == "array" and length >= 5 and . == sort and length == (unique | length)) and
  all(.artifact_paths[];
    type == "string" and
    test("^[A-Za-z0-9._/-]+$") and
    (startswith("/") | not) and
    (split("/") | all(. != "" and . != "." and . != ".."))
  )
' "${marker_file}" >/dev/null

expected_paths=$(mktemp)
actual_paths=$(mktemp)
trap 'rm -f "$expected_paths" "$actual_paths"' EXIT HUP INT TERM
jq -r '.artifact_paths[]' "${marker_file}" > "${expected_paths}"
find "${bundle_dir}" -type f ! -name '.platform-proposal.json' \
  | sed "s#^${bundle_dir}/##" \
  | sort > "${actual_paths}"
if ! cmp -s "${expected_paths}" "${actual_paths}"; then
  echo "Proposal marker paths do not exactly match the materialized files." >&2
  exit 1
fi

proposal_file="${bundle_dir}/environments/proposals/${proposal_id}.json"
test -f "${proposal_file}"
jq -e --arg proposal "${proposal_id}" '
  (keys | sort) == ["installation_id", "mode", "proposal_id", "provider", "request_fingerprint", "request_id", "schema_version", "state"] and
  .schema_version == "proposal.v1" and
  .proposal_id == $proposal and
  (.request_id | type == "string" and test("^env-[0-9a-f]{16}$")) and
  (.request_fingerprint | type == "string" and test("^[0-9a-f]{64}$")) and
  (.installation_id | type == "string" and length > 0) and
  (.provider == "aws" or .provider == "azure") and
  (.mode == "sandbox" or .mode == "enterprise") and
  .state == "ready_for_review"
' "${proposal_file}" >/dev/null

provider=$(jq -er '.provider' "${proposal_file}")
request_id=$(jq -er '.request_id' "${proposal_file}")
tfvars_file="${bundle_dir}/infrastructure/terraform/${provider}/${request_id}.auto.tfvars.json"
test -f "${tfvars_file}"

case "${provider}" in
  aws)
    expected_keys='["desired_nodes","mode","monthly_budget_usd","name_prefix","private_subnet_cidrs","public_subnet_cidrs","region","vpc_cidr"]'
    ;;
  azure)
    expected_keys='["desired_nodes","location","mode","monthly_budget_eur","name_prefix","private_subnet_prefixes","vnet_address_space"]'
    ;;
esac
jq -e --argjson expected "${expected_keys}" --arg mode "$(jq -er '.mode' "${proposal_file}")" '
  type == "object" and (keys | sort) == $expected and .mode == $mode
' "${tfvars_file}" >/dev/null

jq -e --arg proposal_path "environments/proposals/${proposal_id}.json" \
  --arg tfvars_path "infrastructure/terraform/${provider}/${request_id}.auto.tfvars.json" '
  (.artifact_paths | index($proposal_path)) != null and
  (.artifact_paths | index($tfvars_path)) != null
' "${marker_file}" >/dev/null
