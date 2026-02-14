terraform {
  required_version = ">= 1.0"
  
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
  }

  backend "azurerm" {
    # Configure via backend config file or environment variables
    # resource_group_name  = "tfstate-rg"
    # storage_account_name = "tfstatestorage"
    # container_name       = "tfstate"
    # key                  = "retail-datalake.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.environment}-${var.project_name}-rg"
  location = var.location

  tags = var.tags
}

# Key Vault
module "key_vault" {
  source = "./modules/key-vault"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  tags               = var.tags
}

# Data Lake Storage Gen2
module "adls" {
  source = "./modules/adls"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  tags               = var.tags

  depends_on = [azurerm_resource_group.main]
}

# Event Hubs
module "event_hubs" {
  source = "./modules/event-hubs"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  tags               = var.tags

  depends_on = [azurerm_resource_group.main]
}

# Databricks
module "databricks" {
  source = "./modules/databricks"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  adls_storage_id    = module.adls.storage_account_id
  key_vault_id       = module.key_vault.key_vault_id
  tags               = var.tags

  depends_on = [azurerm_resource_group.main, module.adls, module.key_vault]
}

# Synapse Analytics
module "synapse" {
  source = "./modules/synapse"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  adls_storage_id    = module.adls.storage_account_id
  adls_storage_name  = module.adls.storage_account_name
  key_vault_id       = module.key_vault.key_vault_id
  tags               = var.tags

  depends_on = [azurerm_resource_group.main, module.adls, module.key_vault]
}

# Airflow on AKS
module "airflow_aks" {
  source = "./modules/airflow-aks"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  tags               = var.tags

  count = var.deploy_airflow ? 1 : 0

  depends_on = [azurerm_resource_group.main]
}

# Azure Purview
module "purview" {
  source = "./modules/purview"

  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  environment        = var.environment
  project_name       = var.project_name
  tags               = var.tags

  depends_on = [azurerm_resource_group.main]
}

# Data Factory
resource "azurerm_data_factory" "main" {
  name                = "${var.environment}-${var.project_name}-adf"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }

  tags = var.tags
}

# Grant Data Factory access to ADLS
resource "azurerm_role_assignment" "adf_adls" {
  scope                = module.adls.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}

# Log Analytics Workspace for monitoring
resource "azurerm_log_analytics_workspace" "main" {
  name                = "${var.environment}-${var.project_name}-logs"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = var.tags
}

