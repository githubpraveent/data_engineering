output "account_name" {
  description = "Purview account name"
  value       = azurerm_purview_account.main.name
}

output "account_id" {
  description = "Purview account ID"
  value       = azurerm_purview_account.main.id
}

output "catalog_endpoint" {
  description = "Purview catalog endpoint"
  value       = azurerm_purview_account.main.catalog_endpoint
}

