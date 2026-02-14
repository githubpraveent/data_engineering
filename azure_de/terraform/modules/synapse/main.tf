# Synapse Workspace
resource "azurerm_synapse_workspace" "main" {
  name                                 = "${var.environment}-${var.project_name}-synapse"
  resource_group_name                  = var.resource_group_name
  location                             = var.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.synapse.id
  sql_administrator_login              = var.sql_admin_login
  sql_administrator_login_password     = var.sql_admin_password

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# ADLS Gen2 Filesystem for Synapse
resource "azurerm_storage_data_lake_gen2_filesystem" "synapse" {
  name               = "synapse"
  storage_account_id = var.adls_storage_id
}

# SQL Pool (Dedicated SQL Pool)
resource "azurerm_synapse_sql_pool" "main" {
  name                 = "${var.environment}-sqlpool"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  sku_name             = var.sql_pool_sku
  create_mode          = "Default"

  # Auto-pause configuration
  auto_pause {
    delay_in_minutes = 15
  }

  # Auto-scale configuration
  auto_scale {
    max_node_count = 10
    min_node_count = 0
  }

  tags = var.tags
}

# Grant Synapse access to ADLS
resource "azurerm_role_assignment" "synapse_adls" {
  scope                = var.adls_storage_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.main.identity[0].principal_id
}

# Firewall Rules (allow Azure services)
resource "azurerm_synapse_firewall_rule" "allow_azure" {
  name                 = "AllowAzureServices"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

# Private Endpoint (optional, for production)
# resource "azurerm_private_endpoint" "synapse" {
#   name                = "${var.environment}-${var.project_name}-synapse-pe"
#   location            = var.location
#   resource_group_name = var.resource_group_name
#   subnet_id           = var.subnet_id
#
#   private_service_connection {
#     name                           = "synapse-psc"
#     private_connection_resource_id = azurerm_synapse_workspace.main.id
#     subresource_names              = ["Sql"]
#     is_manual_connection           = false
#   }
# }

