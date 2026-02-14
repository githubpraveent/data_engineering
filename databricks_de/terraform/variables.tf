# Terraform variables for Databricks infrastructure

variable "environment" {
  description = "Environment (dev, qa, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be dev, qa, or prod."
  }
}

variable "databricks_host" {
  description = "Databricks workspace host URL"
  type        = string
}

variable "databricks_token" {
  description = "Databricks authentication token"
  type        = string
  sensitive   = true
}

variable "databricks_account_id" {
  description = "Databricks account ID (for multi-workspace setup)"
  type        = string
}

variable "databricks_account_arn" {
  description = "Databricks account ARN (for IAM role assumption)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_zone_id" {
  description = "AWS availability zone"
  type        = string
  default     = "us-east-1a"
}

variable "node_type_id" {
  description = "Databricks node type ID"
  type        = string
  default     = "i3.xlarge"
}

variable "num_workers" {
  description = "Number of worker nodes"
  type        = number
  default     = 2
}

variable "tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}

