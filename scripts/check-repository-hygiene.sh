#!/bin/sh
set -eu

tracked_generated=$(git ls-files | grep -E '(^|/)([^/]+\.tfstate([.][^/]*)?|[^/]+\.tfplan|\.terraform/|node_modules/|site/)' || true)
if [ -n "$tracked_generated" ]; then
  printf '%s\n' "generated or sensitive infrastructure artifact is tracked:" >&2
  printf '%s\n' "$tracked_generated" >&2
  exit 1
fi

tracked_private_variables=$(git ls-files | grep -E '(^|/)[^/]+\.tfvars(\.json)?$' | grep -Ev '^examples/' || true)
if [ -n "$tracked_private_variables" ]; then
  printf '%s\n' "private Terraform variable file is tracked:" >&2
  printf '%s\n' "$tracked_private_variables" >&2
  exit 1
fi

credential_pattern='(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|ARM_CLIENT_SECRET|AZURE_CLIENT_SECRET|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)'
if git grep -n -E "$credential_pattern" -- ':!scripts/check-repository-hygiene.sh' >/dev/null 2>&1; then
  printf '%s\n' 'credential-like content found in tracked files' >&2
  exit 1
fi

printf '%s\n' 'Repository hygiene checks passed.'
