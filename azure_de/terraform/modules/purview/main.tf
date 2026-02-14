# Purview Account
resource "azurerm_purview_account" "main" {
  name                = "${var.environment}-${var.project_name}-purview"
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Grant Purview access to ADLS (for scanning)
# This would typically be done via Purview UI or separate role assignments
# resource "azurerm_role_assignment" "purview_adls" {
#   scope                = var.adls_storage_id
#   role_definition_name = "Storage Blob Data Reader"
#   principal_id         = azurerm_purview_account.main.identity[0].principal_id
# }

