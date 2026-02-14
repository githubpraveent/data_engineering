output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "adls_storage_account_name" {
  description = "ADLS Gen2 storage account name"
  value       = module.adls.storage_account_name
}

output "adls_storage_account_id" {
  description = "ADLS Gen2 storage account ID"
  value       = module.adls.storage_account_id
}

output "adls_containers" {
  description = "ADLS container names"
  value       = module.adls.container_names
}

output "event_hubs_namespace" {
  description = "Event Hubs namespace name"
  value       = module.event_hubs.namespace_name
}

output "databricks_workspace_url" {
  description = "Databricks workspace URL"
  value       = module.databricks.workspace_url
}

output "synapse_workspace_name" {
  description = "Synapse workspace name"
  value       = module.synapse.workspace_name
}

output "synapse_sql_pool_name" {
  description = "Synapse SQL Pool name"
  value       = module.synapse.sql_pool_name
}

output "airflow_url" {
  description = "Airflow web UI URL"
  value       = var.deploy_airflow ? module.airflow_aks[0].airflow_url : null
}

output "purview_account_name" {
  description = "Purview account name"
  value       = module.purview.account_name
}

output "key_vault_name" {
  description = "Key Vault name"
  value       = module.key_vault.key_vault_name
}

output "data_factory_name" {
  description = "Data Factory name"
  value       = azurerm_data_factory.main.name
}

output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.main.workspace_id
}

