output "workspace_name" {
  description = "Synapse workspace name"
  value       = azurerm_synapse_workspace.main.name
}

output "workspace_id" {
  description = "Synapse workspace ID"
  value       = azurerm_synapse_workspace.main.id
}

output "sql_pool_name" {
  description = "SQL Pool name"
  value       = azurerm_synapse_sql_pool.main.name
}

output "sql_pool_id" {
  description = "SQL Pool ID"
  value       = azurerm_synapse_sql_pool.main.id
}

