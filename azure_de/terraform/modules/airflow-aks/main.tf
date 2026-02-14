# AKS Cluster
resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.environment}-${var.project_name}-aks"
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = "${var.environment}-${var.project_name}-aks"
  kubernetes_version  = "1.28"

  default_node_pool {
    name                = "default"
    node_count          = var.node_count
    vm_size             = var.vm_size
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 10
    os_disk_size_gb     = 50
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
  }

  tags = var.tags
}

# Azure Container Registry (for Airflow images)
resource "azurerm_container_registry" "main" {
  name                = "${var.environment}${var.project_name}acr"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Standard"
  admin_enabled       = true

  tags = var.tags
}

# Grant AKS access to ACR
resource "azurerm_role_assignment" "aks_acr" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id
}

# Storage Account for Airflow (DAGs, logs)
resource "azurerm_storage_account" "airflow" {
  name                     = "${var.environment}${var.project_name}airflow"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_storage_share" "airflow_dags" {
  name                 = "airflow-dags"
  storage_account_name = azurerm_storage_account.airflow.name
  quota                = 5
}

resource "azurerm_storage_share" "airflow_logs" {
  name                 = "airflow-logs"
  storage_account_name = azurerm_storage_account.airflow.name
  quota                = 10
}

# Azure Database for PostgreSQL (for Airflow metadata)
resource "azurerm_postgresql_flexible_server" "airflow" {
  name                   = "${var.environment}-${var.project_name}-airflow-db"
  resource_group_name    = var.resource_group_name
  location               = var.location
  version                = "14"
  administrator_login    = var.postgres_admin_login
  administrator_password = var.postgres_admin_password
  sku_name               = "B_Standard_B1ms"

  storage_mb = 32768
  backup_retention_days = 7

  tags = var.tags
}

resource "azurerm_postgresql_flexible_server_database" "airflow" {
  name      = "airflow"
  server_id = azurerm_postgresql_flexible_server.airflow.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

# Firewall rule to allow AKS access
resource "azurerm_postgresql_flexible_server_firewall_rule" "allow_aks" {
  name             = "AllowAKS"
  server_id        = azurerm_postgresql_flexible_server.airflow.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "255.255.255.255"
}

