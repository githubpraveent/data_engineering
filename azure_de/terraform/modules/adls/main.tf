# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "${var.environment}${var.project_name}adls"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = var.account_tier
  account_replication_type  = var.account_replication
  account_kind             = "StorageV2"
  is_hns_enabled           = true # Enable Data Lake Storage Gen2
  min_tls_version          = "TLS1_2"

  # Enable soft delete
  blob_properties {
    delete_retention_policy {
      days = 30
    }
    versioning_enabled = true
  }

  # Lifecycle management
  lifecycle {
    ignore_changes = [
      tags
    ]
  }

  tags = var.tags
}

# Containers for Medallion Architecture
resource "azurerm_storage_container" "bronze" {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "silver" {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "gold" {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "staging" {
  name                  = "staging"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Lifecycle Management Policy
resource "azurerm_storage_management_policy" "main" {
  storage_account_id = azurerm_storage_account.main.id

  rule {
    name    = "MoveToCoolAfter30Days"
    enabled = true
    filters {
      blob_types = ["blockBlob"]
      prefix_match = ["bronze/", "silver/", "gold/"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = 30
      }
    }
  }

  rule {
    name    = "MoveToArchiveAfter90Days"
    enabled = true
    filters {
      blob_types = ["blockBlob"]
      prefix_match = ["bronze/"]
    }
    actions {
      base_blob {
        tier_to_archive_after_days_since_modification_greater_than = 90
      }
    }
  }

  rule {
    name    = "DeleteAfter365Days"
    enabled = true
    filters {
      blob_types = ["blockBlob"]
      prefix_match = ["bronze/"]
    }
    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 365
      }
    }
  }
}

