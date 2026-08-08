output "provider" {
  value = "azure"
}

output "mode" {
  value = var.mode
}

output "resource_group_name" {
  value = azurerm_resource_group.platform.name
}

output "vnet_id" {
  value = module.network.vnet_id
}

output "private_subnet_ids" {
  value = module.network.private_subnet_ids
}

output "cluster_name" {
  value = module.aks_platform.cluster_name
}

output "cluster_endpoint_private" {
  value       = true
  description = "The stack contract requires a private-only Kubernetes endpoint."
}

output "log_workspace_id" {
  value = module.security_logging.log_workspace_id
}
