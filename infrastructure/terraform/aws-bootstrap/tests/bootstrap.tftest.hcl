mock_provider "aws" {}

variables {
  state_bucket_name          = "example-platform-state"
  github_repository          = "example-org/example-platform"
  github_plan_environment    = "platform-plan"
  github_apply_environment   = "platform-apply"
  github_destroy_environment = "platform-destroy"
}

run "encrypted_native_lockfile_state_plan" {
  command = plan

  assert {
    condition     = output.state_bucket_name == "example-platform-state"
    error_message = "Bootstrap must preserve the operator-provided state bucket name."
  }

  assert {
    condition     = output.native_lockfile_enabled
    error_message = "Bootstrap must expose native S3 lockfile support."
  }

  assert {
    condition     = output.github_oidc_subjects.apply == "repo:example-org/example-platform:environment:platform-apply"
    error_message = "Bootstrap apply identity must use an exact GitHub Environment subject."
  }

  assert {
    condition     = length(output.github_oidc_role_arns) == 3
    error_message = "Bootstrap must create separate plan, apply, and destroy roles."
  }
}
