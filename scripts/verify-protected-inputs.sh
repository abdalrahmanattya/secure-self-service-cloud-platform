#!/bin/sh
set -eu

: "${PROTECTED_OPERATION:?PROTECTED_OPERATION is required}"
: "${COMMIT_SHA:?COMMIT_SHA is required}"
: "${TF_PROVIDER:?TF_PROVIDER is required}"
: "${TF_MODE:?TF_MODE is required}"
: "${REQUEST_ID:?REQUEST_ID is required}"
: "${PROPOSAL_ID:?PROPOSAL_ID is required}"
: "${REVIEWER:?REVIEWER is required}"
: "${REQUESTER:?REQUESTER is required}"

case "${PROTECTED_OPERATION}" in plan|apply|rollback|drift|destroy|destroy-apply) ;; *) exit 2 ;; esac
printf '%s\n' "${COMMIT_SHA}" | grep -Eq '^[0-9a-fA-F]{40}$'
printf '%s\n' "${COMMIT_SHA}" | grep -Fxq "${GITHUB_SHA:-${COMMIT_SHA}}"
printf '%s\n' "${TF_PROVIDER}" | grep -Eq '^(aws|azure)$'
printf '%s\n' "${TF_MODE}" | grep -Eq '^(sandbox|enterprise)$'
printf '%s\n' "${REQUEST_ID}" | grep -Eq '^[a-z0-9][a-z0-9-]{7,63}$'
printf '%s\n' "${PROPOSAL_ID}" | grep -Eq '^[a-z0-9][a-z0-9-]{7,63}$'
test -n "${REVIEWER}" && test -n "${REQUESTER}"
test "${REVIEWER}" != "${REQUESTER}" && test "${REVIEWER}" != "${GITHUB_ACTOR:-}"
printf '%s\n' "${PROPOSAL_SHA256}" | grep -Eq '^[0-9a-fA-F]{64}$'
if [ -n "${PLAN_SHA256:-}" ]; then printf '%s\n' "${PLAN_SHA256}" | grep -Eq '^[0-9a-fA-F]{64}$'; fi
if [ "${PROTECTED_OPERATION}" = destroy ] || [ "${PROTECTED_OPERATION}" = destroy-apply ]; then
  test "${DESTROY_CONFIRMATION}" = "DESTROY ${TF_PROVIDER}/${TF_MODE}/${PROPOSAL_ID}"
  test "${DESTROY_SECOND_CONFIRMATION}" = "DESTROY CONFIRMED ${TF_PROVIDER}/${TF_MODE}/${PROPOSAL_ID}"
elif [ "${PROTECTED_OPERATION}" = apply ]; then
  test "${LIFECYCLE_CONFIRMATION}" = "APPLY ${TF_PROVIDER}/${TF_MODE}/${PROPOSAL_ID}"
elif [ "${PROTECTED_OPERATION}" = rollback ]; then
  test "${LIFECYCLE_CONFIRMATION}" = "ROLLBACK ${TF_PROVIDER}/${TF_MODE}/${PROPOSAL_ID}"
fi
