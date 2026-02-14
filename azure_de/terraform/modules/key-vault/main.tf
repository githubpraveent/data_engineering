# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "${var.environment}-${var.project_name}-kv"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Network ACLs (adjust for production)
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  # Enable soft delete
  soft_delete_retention_days = 7
  purge_protection_enabled   = false # Set to true for production

  tags = var.tags
}

# Access policy for current user/service principal
resource "azurerm_key_vault_access_policy" "current_user" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  key_permissions = [
    "Get", "List", "Create", "Delete", "Update", "Recover", "Backup", "Restore"
  ]

  secret_permissions = [
    "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
  ]

  certificate_permissions = [
    "Get", "List", "Create", "Delete", "Update", "Recover", "Backup", "Restore"
  ]
}

data "azurerm_client_config" "current" {}

