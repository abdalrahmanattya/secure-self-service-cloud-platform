output "client_ids" {
  value = { for lifecycle, identity in azurerm_user_assigned_identity.github : lifecycle => identity.client_id }
}

output "subjects" {
  value = { for lifecycle, environment in local.lifecycle_environments : lifecycle => "repo:${var.github_repository}:environment:${environment}" }
}
