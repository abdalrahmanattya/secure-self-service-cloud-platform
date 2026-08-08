locals {
  common_tags = {
    managed-by   = "terraform"
    platform     = "secure-self-service-cloud-platform"
    installation = var.mode
  }
}

resource "azurerm_resource_group" "platform" {
  name     = "${var.name_prefix}-rg"
  location = var.location
  tags     = local.common_tags
}

module "network" {
  source = "./modules/network"

  resource_group_name = azurerm_resource_group.platform.name
  location            = var.location
  name_prefix         = var.name_prefix
  address_space       = var.vnet_address_space
  subnet_prefixes     = var.private_subnet_prefixes
  tags                = local.common_tags
}

module "security_logging" {
  source = "./modules/security-logging"

  resource_group_name = azurerm_resource_group.platform.name
  location            = var.location
  name_prefix         = var.name_prefix
  tenant_id           = var.tenant_id
  tags                = local.common_tags
}

module "aks_platform" {
  source = "./modules/aks-platform"

  resource_group_name = azurerm_resource_group.platform.name
  location            = var.location
  cluster_name        = "${var.name_prefix}-aks"
  kubernetes_version  = var.kubernetes_version
  subnet_id           = module.network.private_subnet_ids[0]
  log_workspace_id    = module.security_logging.log_workspace_id
  tags                = local.common_tags
  node_vm_size        = var.node_vm_size
  desired_nodes       = var.desired_nodes
  tenant_id           = var.tenant_id
}

module "budget_guardrails" {
  source = "./modules/budget-guardrails"

  resource_group_id  = azurerm_resource_group.platform.id
  name_prefix        = var.name_prefix
  monthly_budget_eur = var.monthly_budget_eur
  alert_email        = var.budget_alert_email
}
