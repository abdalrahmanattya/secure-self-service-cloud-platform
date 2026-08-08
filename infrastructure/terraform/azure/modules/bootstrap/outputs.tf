output "container_name" {
  value = local.state_container_name
}

output "storage_account_name" {
  value = var.storage_account_name
}

output "github_identity_client_ids" {
  value = module.github_oidc.client_ids
}

output "github_oidc_subjects" {
  value = module.github_oidc.subjects
}
