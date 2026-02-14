variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be dev, qa, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "retail-datalake"
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "RetailDataLake"
    ManagedBy   = "Terraform"
    Environment = ""
  }
}

variable "deploy_airflow" {
  description = "Whether to deploy Airflow on AKS"
  type        = bool
  default     = true
}

# ADLS Variables
variable "adls_tier" {
  description = "Storage account tier (Standard or Premium)"
  type        = string
  default     = "Standard"
}

variable "adls_replication" {
  description = "Storage account replication type"
  type        = string
  default     = "ZRS"
}

# Event Hubs Variables
variable "event_hub_sku" {
  description = "Event Hubs namespace SKU (Basic, Standard, Premium)"
  type        = string
  default     = "Standard"
}

variable "event_hub_capacity" {
  description = "Event Hubs throughput units"
  type        = number
  default     = 1
}

# Databricks Variables
variable "databricks_sku" {
  description = "Databricks SKU (standard or premium)"
  type        = string
  default     = "premium"
}

# Synapse Variables
variable "synapse_sql_pool_sku" {
  description = "Synapse SQL Pool SKU"
  type        = string
  default     = "DW100c"
}

variable "synapse_sql_pool_min_capacity" {
  description = "Minimum capacity for SQL Pool (auto-pause threshold)"
  type        = number
  default     = 0.5
}

# AKS Variables (for Airflow)
variable "aks_node_count" {
  description = "Number of nodes in AKS cluster"
  type        = number
  default     = 3
}

variable "aks_vm_size" {
  description = "VM size for AKS nodes"
  type        = string
  default     = "Standard_D4s_v3"
}

