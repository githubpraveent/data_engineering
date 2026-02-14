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

variable "account_tier" {
  description = "Storage account tier"
  type        = string
  default     = "Standard"
}

variable "account_replication" {
  description = "Storage account replication type"
  type        = string
  default     = "ZRS"
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

