variable "resource_group_name" {
  description = "Resource group name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "sku" {
  description = "Databricks SKU"
  type        = string
  default     = "premium"
}

variable "adls_storage_id" {
  description = "ADLS storage account ID"
  type        = string
}

variable "key_vault_id" {
  description = "Key Vault ID for CMK"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

