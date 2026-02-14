output "aks_cluster_name" {
  description = "AKS cluster name"
  value       = azurerm_kubernetes_cluster.main.name
}

output "aks_cluster_id" {
  description = "AKS cluster ID"
  value       = azurerm_kubernetes_cluster.main.id
}

output "kube_config" {
  description = "Kubernetes config (sensitive)"
  value       = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive   = true
}

output "airflow_url" {
  description = "Airflow web UI URL (to be configured after deployment)"
  value       = "https://${azurerm_kubernetes_cluster.main.fqdn}"
}

output "postgres_host" {
  description = "PostgreSQL host"
  value       = azurerm_postgresql_flexible_server.airflow.fqdn
}

output "storage_account_name" {
  description = "Storage account name for Airflow"
  value       = azurerm_storage_account.airflow.name
}

