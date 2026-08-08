output "vnet_id" {
  value = azurerm_virtual_network.this.id
}

output "private_subnet_ids" {
  value = azurerm_subnet.private[*].id
}
