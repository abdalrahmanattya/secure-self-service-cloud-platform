output "state_bucket_name" {
  value = module.state.state_bucket_name
}

output "native_lockfile_enabled" {
  value       = true
  description = "Terraform S3 backend uses native lockfile support; no legacy table is required."
}

output "state_kms_key_arn" {
  value       = module.state.kms_key_arn
  description = "KMS key used for encrypted Terraform state."
}

output "github_oidc_role_arns" {
  value       = module.state.github_oidc_role_arns
  description = "Bootstrap-created plan/apply/destroy roles used by protected workflows."
}

output "github_oidc_subjects" {
  value = module.state.github_oidc_subjects
}
