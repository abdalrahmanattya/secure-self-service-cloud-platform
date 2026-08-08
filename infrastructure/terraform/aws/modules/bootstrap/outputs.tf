output "state_bucket_name" {
  value = var.state_bucket_name
}

output "kms_key_arn" {
  value = aws_kms_key.state.arn
}

output "github_oidc_role_arns" {
  value = module.github_oidc.role_arns
}

output "github_oidc_subjects" {
  value = module.github_oidc.subjects
}
