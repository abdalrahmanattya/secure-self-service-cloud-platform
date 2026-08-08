#!/bin/sh
set -eu
: "${OIDC_PROVIDER:?OIDC_PROVIDER is required}"
: "${OIDC_AUDIENCE:?OIDC_AUDIENCE is required}"
: "${ACTIONS_ID_TOKEN_REQUEST_TOKEN:?GitHub OIDC request token is unavailable}"
: "${ACTIONS_ID_TOKEN_REQUEST_URL:?GitHub OIDC request URL is unavailable}"
token_response=$(curl --fail --silent --show-error -H "Authorization: bearer ${ACTIONS_ID_TOKEN_REQUEST_TOKEN}" "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=${OIDC_AUDIENCE}")
oidc_token=$(printf '%s' "${token_response}" | jq -er '.value')

case "${OIDC_PROVIDER}" in
  aws)
    : "${OIDC_ROLE_ARN:?OIDC_ROLE_ARN is required for AWS}"
    credentials=$(aws sts assume-role-with-web-identity --role-arn "${OIDC_ROLE_ARN}" --role-session-name "platform-${GITHUB_RUN_ID}" --web-identity-token "${oidc_token}" --duration-seconds 3600)
    {
      printf 'AWS_%s=%s\n' 'ACCESS_KEY_ID' "$(printf '%s' "${credentials}" | jq -er '.Credentials.AccessKeyId')"
      printf 'AWS_%s=%s\n' 'SECRET_ACCESS_KEY' "$(printf '%s' "${credentials}" | jq -er '.Credentials.SecretAccessKey')"
      printf 'AWS_SESSION_TOKEN=%s\n' "$(printf '%s' "${credentials}" | jq -er '.Credentials.SessionToken')"
    } >> "${GITHUB_ENV}"
    ;;
  azure)
    : "${AZURE_CLIENT_ID:?AZURE_CLIENT_ID is required for Azure}"
    : "${AZURE_TENANT_ID:?AZURE_TENANT_ID is required for Azure}"
    : "${AZURE_SUBSCRIPTION_ID:?AZURE_SUBSCRIPTION_ID is required for Azure}"
    az login --service-principal --username "${AZURE_CLIENT_ID}" --tenant "${AZURE_TENANT_ID}" --federated-token "${oidc_token}" --allow-no-subscriptions >/dev/null
    az account set --subscription "${AZURE_SUBSCRIPTION_ID}"
    {
      printf 'ARM_USE_OIDC=true\n'
      printf 'ARM_USE_AZUREAD=true\n'
      printf 'ARM_CLIENT_ID=%s\n' "${AZURE_CLIENT_ID}"
      printf 'ARM_TENANT_ID=%s\n' "${AZURE_TENANT_ID}"
      printf 'ARM_SUBSCRIPTION_ID=%s\n' "${AZURE_SUBSCRIPTION_ID}"
      printf 'ARM_OIDC_TOKEN=%s\n' "${oidc_token}"
    } >> "${GITHUB_ENV}"
    ;;
  *) exit 2 ;;
esac
