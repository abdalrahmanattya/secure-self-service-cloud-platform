mock_provider "azurerm" {}

variables {
  resource_group_name      = "example-platform-bootstrap"
  storage_account_name     = "exampleplatformstate"
  deployment_scope_id      = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-platform"
  trusted_bootstrap_access = true
  github_repository        = "example-org/example-platform"
  github_environment       = "platform"
}

run "encrypted_state_plan" {
  command = plan

  assert {
    condition     = output.storage_account_name == "exampleplatformstate"
    error_message = "Bootstrap must preserve the operator-provided state account name."
  }

  assert {
    condition     = output.github_oidc_subjects.apply == "repo:example-org/example-platform:environment:platform-apply"
    error_message = "Bootstrap apply identity must use an exact GitHub Environment subject."
  }

  assert {
    condition     = length(output.github_identity_client_ids) == 3
    error_message = "Bootstrap must create separate plan, apply, and destroy identities."
  }
}
