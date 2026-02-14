# Variables are defined in main.tf
# This file can be used for additional variable definitions if needed

variable "snowflake_username" {
  description = "Snowflake username"
  type        = string
}

variable "snowflake_password" {
  description = "Snowflake password"
  type        = string
  sensitive   = true
}

variable "snowflake_account" {
  description = "Snowflake account identifier"
  type        = string
}

variable "snowflake_region" {
  description = "Snowflake region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment (DEV, QA, PROD)"
  type        = string
  default     = "DEV"
}

