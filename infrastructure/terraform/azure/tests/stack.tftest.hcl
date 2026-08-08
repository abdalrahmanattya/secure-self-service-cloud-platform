mock_provider "azurerm" {}
mock_provider "azuread" {}

variables {
  mode               = "simulation"
  name_prefix        = "example-platform"
  tenant_id          = "00000000-0000-0000-0000-000000000000"
  subscription_id    = "00000000-0000-0000-0000-000000000000"
  budget_alert_email = ""
}

run "private_encrypted_stack_plan" {
  command = plan

  assert {
    condition     = output.provider == "azure"
    error_message = "The Azure root stack must identify itself as Azure."
  }

  assert {
    condition     = output.cluster_endpoint_private
    error_message = "The Azure stack must expose a private-only Kubernetes contract."
  }

}
