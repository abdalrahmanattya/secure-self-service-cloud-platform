output "log_workspace_id" {
  value = azurerm_log_analytics_workspace.this.id
}

output "key_vault_id" {
  value = azurerm_key_vault.this.id
}
