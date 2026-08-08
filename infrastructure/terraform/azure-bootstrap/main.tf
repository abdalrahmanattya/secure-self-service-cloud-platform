resource "azurerm_resource_group" "bootstrap" {
  name     = var.resource_group_name
  location = var.location
  tags     = { managed-by = "operator-run-bootstrap" }
}

module "state" {
  source = "../azure/modules/bootstrap"

  location                   = var.location
  resource_group_name        = azurerm_resource_group.bootstrap.name
  storage_account_name       = var.storage_account_name
  trusted_bootstrap_access   = var.trusted_bootstrap_access
  private_endpoint_subnet_id = var.private_endpoint_subnet_id
  private_dns_zone_ids       = var.private_dns_zone_ids
  deployment_scope_id        = var.deployment_scope_id
  github_repository          = var.github_repository
  github_environment         = var.github_environment
}
