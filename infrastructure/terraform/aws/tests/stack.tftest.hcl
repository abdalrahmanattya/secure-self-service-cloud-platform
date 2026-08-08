mock_provider "aws" {}

variables {
  mode               = "simulation"
  name_prefix        = "example-platform"
  region             = "eu-west-1"
  budget_alert_email = ""
}

run "private_encrypted_stack_plan" {
  command = plan

  assert {
    condition     = output.provider == "aws"
    error_message = "The AWS root stack must identify itself as AWS."
  }

  assert {
    condition     = output.cluster_endpoint_private
    error_message = "The AWS stack must expose a private-only Kubernetes contract."
  }

}
