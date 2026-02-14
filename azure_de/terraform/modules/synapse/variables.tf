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

variable "adls_storage_id" {
  description = "ADLS storage account ID"
  type        = string
}

variable "adls_storage_name" {
  description = "ADLS storage account name"
  type        = string
}

variable "sql_admin_login" {
  description = "SQL administrator login"
  type        = string
  default     = "sqladmin"
}

variable "sql_admin_password" {
  description = "SQL administrator password (should use Key Vault)"
  type        = string
  sensitive   = true
}

variable "sql_pool_sku" {
  description = "SQL Pool SKU"
  type        = string
  default     = "DW100c"
}

variable "key_vault_id" {
  description = "Key Vault ID"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

