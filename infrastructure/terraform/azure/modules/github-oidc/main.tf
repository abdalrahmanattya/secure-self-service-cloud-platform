locals {
  lifecycle_environments = {
    plan    = "${var.github_environment}-plan"
    apply   = "${var.github_environment}-apply"
    destroy = "${var.github_environment}-destroy"
  }

  lifecycle_actions = {
    plan = [
      "Microsoft.Resources/subscriptions/resourceGroups/read",
      "Microsoft.Resources/deployments/read",
      "Microsoft.Storage/storageAccounts/read",
      "Microsoft.ContainerService/managedClusters/read",
      "Microsoft.Network/*/read",
      "Microsoft.OperationalInsights/workspaces/read",
      "Microsoft.KeyVault/vaults/read",
      "Microsoft.Insights/*/read",
      "Microsoft.Consumption/*/read"
    ]
    apply = [
      "Microsoft.Resources/subscriptions/resourceGroups/*",
      "Microsoft.Resources/deployments/*",
      "Microsoft.Storage/storageAccounts/*",
      "Microsoft.ContainerService/managedClusters/*",
      "Microsoft.Network/*",
      "Microsoft.OperationalInsights/workspaces/*",
      "Microsoft.KeyVault/vaults/*",
      "Microsoft.Insights/*",
      "Microsoft.Consumption/*"
    ]
    destroy = [
      "Microsoft.Resources/subscriptions/resourceGroups/*",
      "Microsoft.Resources/deployments/*",
      "Microsoft.Storage/storageAccounts/*",
      "Microsoft.ContainerService/managedClusters/*",
      "Microsoft.Network/*",
      "Microsoft.OperationalInsights/workspaces/*",
      "Microsoft.KeyVault/vaults/*",
      "Microsoft.Insights/*",
      "Microsoft.Consumption/*"
    ]
  }

  lifecycle_data_actions = {
    plan    = ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"]
    apply   = ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read", "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write", "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete"]
    destroy = ["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read", "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write", "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/delete"]
  }
}

resource "azurerm_user_assigned_identity" "github" {
  for_each            = local.lifecycle_environments
  name                = "${var.name_prefix}-github-${each.key}"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = merge(var.tags, { lifecycle = each.key })
}

resource "azurerm_federated_identity_credential" "github" {
  for_each                  = local.lifecycle_environments
  name                      = "${var.name_prefix}-github-${each.key}"
  user_assigned_identity_id = azurerm_user_assigned_identity.github[each.key].id
  audience                  = ["api://AzureADTokenExchange"]
  issuer                    = "https://token.actions.githubusercontent.com"
  subject                   = "repo:${var.github_repository}:environment:${each.value}"
}

resource "azurerm_role_definition" "github" {
  for_each          = local.lifecycle_actions
  name              = "${var.name_prefix}-github-${each.key}"
  scope             = var.deployment_scope_id
  description       = "Bounded ${each.key} role for protected platform lifecycle workflows."
  assignable_scopes = [var.deployment_scope_id]

  permissions {
    actions          = each.value
    not_actions      = []
    data_actions     = local.lifecycle_data_actions[each.key]
    not_data_actions = []
  }
}

resource "azurerm_role_assignment" "github" {
  for_each           = local.lifecycle_environments
  scope              = var.deployment_scope_id
  role_definition_id = azurerm_role_definition.github[each.key].role_definition_resource_id
  principal_id       = azurerm_user_assigned_identity.github[each.key].principal_id
}
