locals {
  state_container_name = "tfstate"
}

resource "azurerm_storage_account" "state" {
  name                              = var.storage_account_name
  resource_group_name               = var.resource_group_name
  location                          = var.location
  account_tier                      = "Standard"
  account_replication_type          = "ZRS"
  min_tls_version                   = "TLS1_2"
  https_traffic_only_enabled        = true
  allow_nested_items_to_be_public   = false
  public_network_access_enabled     = var.trusted_bootstrap_access
  infrastructure_encryption_enabled = true
  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
    container_delete_retention_policy {
      days = 30
    }
  }
  tags = { managed-by = "operator-run-bootstrap" }
}

resource "azurerm_storage_container" "state" {
  name                  = local.state_container_name
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

resource "azurerm_private_endpoint" "state" {
  count               = var.trusted_bootstrap_access ? 0 : 1
  name                = "${var.storage_account_name}-blob-private-endpoint"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "${var.storage_account_name}-blob-connection"
    private_connection_resource_id = azurerm_storage_account.state.id
    is_manual_connection           = false
    subresource_names              = ["blob"]
  }

  private_dns_zone_group {
    name                 = "blob-dns"
    private_dns_zone_ids = var.private_dns_zone_ids
  }
}

module "github_oidc" {
  source = "../github-oidc"

  resource_group_name = var.resource_group_name
  location            = var.location
  name_prefix         = var.storage_account_name
  deployment_scope_id = var.deployment_scope_id
  github_repository   = var.github_repository
  github_environment  = var.github_environment
}
