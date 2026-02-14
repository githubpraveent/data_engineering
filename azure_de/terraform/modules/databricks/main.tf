# Databricks Workspace
resource "azurerm_databricks_workspace" "main" {
  name                = "${var.environment}-${var.project_name}-dbw"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = var.sku

  managed_services_cmk_key_vault_key_id = var.key_vault_id != null ? "${var.key_vault_id}/keys/databricks-cmk" : null

  custom_parameters {
    no_public_ip = false
    public_subnet_name = null
    private_subnet_name = null
    virtual_network_id = null
  }

  tags = var.tags
}

# Note: Service Principal for Databricks would be created separately
# or via Azure AD app registration if needed

# Grant Databricks access to ADLS
resource "azurerm_role_assignment" "databricks_adls" {
  scope                = var.adls_storage_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_workspace.main.identity[0].principal_id
}

# Databricks Cluster Configuration (via Databricks provider)
provider "databricks" {
  host = azurerm_databricks_workspace.main.workspace_url
}

# Standard Cluster for batch jobs
resource "databricks_cluster" "standard" {
  cluster_name            = "${var.environment}-standard-cluster"
  spark_version           = "13.3.x-scala2.12"
  node_type_id            = "Standard_DS3_v2"
  driver_node_type_id     = "Standard_DS3_v2"
  autotermination_minutes = 20
  enable_elastic_disk     = true

  autoscale {
    min_workers = 1
    max_workers = 4
  }

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
    "spark.databricks.delta.optimizeWrite.enabled" = "true"
    "spark.databricks.delta.autoCompact.enabled" = "true"
  }

  custom_tags = var.tags
}

# High Concurrency Cluster for interactive analysis
resource "databricks_cluster" "high_concurrency" {
  cluster_name            = "${var.environment}-high-concurrency-cluster"
  spark_version           = "13.3.x-scala2.12"
  node_type_id            = "Standard_DS3_v2"
  driver_node_type_id     = "Standard_DS3_v2"
  autotermination_minutes = 30
  enable_elastic_disk     = true

  autoscale {
    min_workers = 2
    max_workers = 8
  }

  spark_conf = {
    "spark.databricks.delta.preview.enabled" = "true"
    "spark.databricks.delta.optimizeWrite.enabled" = "true"
    "spark.databricks.delta.autoCompact.enabled" = "true"
  }

  custom_tags = var.tags
}

