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
  description = "Event Hubs SKU"
  type        = string
  default     = "Standard"
}

variable "capacity" {
  description = "Throughput units"
  type        = number
  default     = 1
}

variable "max_throughput_units" {
  description = "Maximum throughput units for auto-inflate"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}

