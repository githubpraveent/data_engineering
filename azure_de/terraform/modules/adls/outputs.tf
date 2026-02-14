output "storage_account_name" {
  description = "Storage account name"
  value       = azurerm_storage_account.main.name
}

output "storage_account_id" {
  description = "Storage account ID"
  value       = azurerm_storage_account.main.id
}

output "storage_account_primary_dfs_endpoint" {
  description = "Primary DFS endpoint"
  value       = azurerm_storage_account.main.primary_dfs_endpoint
}

output "container_names" {
  description = "Container names"
  value = {
    bronze   = azurerm_storage_container.bronze.name
    silver   = azurerm_storage_container.silver.name
    gold     = azurerm_storage_container.gold.name
    staging  = azurerm_storage_container.staging.name
  }
}

