output "state_container_name" {
  value = module.state.container_name
}

output "storage_account_name" {
  value = module.state.storage_account_name
}

output "github_identity_client_ids" {
  value       = module.state.github_identity_client_ids
  description = "Bootstrap-created plan/apply/destroy identities used by protected workflows."
}

output "github_oidc_subjects" {
  value = module.state.github_oidc_subjects
}
