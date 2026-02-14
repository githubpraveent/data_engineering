# ============================================================================
# Terraform Configuration for Snowflake Infrastructure
# Provisions Snowflake warehouses, databases, and roles
# ============================================================================

terraform {
  required_providers {
    snowflake = {
      source  = "Snowflake-Labs/snowflake"
      version = "~> 0.76"
    }
  }
}

provider "snowflake" {
  username = var.snowflake_username
  password = var.snowflake_password
  account  = var.snowflake_account
  region   = var.snowflake_region
}

# ============================================================================
# Variables
# ============================================================================

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

# ============================================================================
# Warehouses
# ============================================================================

resource "snowflake_warehouse" "wh_ingest" {
  name           = "WH_INGEST"
  warehouse_size = "SMALL"
  auto_suspend   = 60
  auto_resume    = true
  initially_suspended = true
  comment        = "Warehouse for data ingestion workloads"
}

resource "snowflake_warehouse" "wh_trans" {
  name           = "WH_TRANS"
  warehouse_size = "MEDIUM"
  auto_suspend   = 300
  auto_resume    = true
  initially_suspended = true
  comment        = "Warehouse for transformation workloads"
}

resource "snowflake_warehouse" "wh_analyt" {
  name           = "WH_ANALYT"
  warehouse_size = "LARGE"
  auto_suspend   = 600
  auto_resume    = true
  initially_suspended = true
  comment        = "Warehouse for analytics and reporting workloads"
}

resource "snowflake_warehouse" "wh_load" {
  name           = "WH_LOAD"
  warehouse_size = "X-LARGE"
  auto_suspend   = 300
  auto_resume    = true
  initially_suspended = true
  comment        = "Warehouse for bulk data loading operations"
}

# ============================================================================
# Databases
# ============================================================================

resource "snowflake_database" "raw_db" {
  name    = "${var.environment}_RAW"
  comment = "Raw landing database for ${var.environment} environment"
}

resource "snowflake_database" "staging_db" {
  name    = "${var.environment}_STAGING"
  comment = "Staging database for ${var.environment} environment"
}

resource "snowflake_database" "dw_db" {
  name    = "${var.environment}_DW"
  comment = "Data warehouse database for ${var.environment} environment"
}

# ============================================================================
# Schemas
# ============================================================================

resource "snowflake_schema" "bronze_schema" {
  database = snowflake_database.raw_db.name
  name     = "BRONZE"
  comment  = "Bronze layer schema for raw data"
}

resource "snowflake_schema" "silver_schema" {
  database = snowflake_database.staging_db.name
  name     = "SILVER"
  comment  = "Silver layer schema for cleaned data"
}

resource "snowflake_schema" "dimensions_schema" {
  database = snowflake_database.dw_db.name
  name     = "DIMENSIONS"
  comment  = "Dimensions schema for dimensional model"
}

resource "snowflake_schema" "facts_schema" {
  database = snowflake_database.dw_db.name
  name     = "FACTS"
  comment  = "Facts schema for fact tables"
}

# ============================================================================
# Roles
# ============================================================================

resource "snowflake_role" "data_engineer" {
  name    = "DATA_ENGINEER"
  comment = "Role for data engineering team"
}

resource "snowflake_role" "data_analyst" {
  name    = "DATA_ANALYST"
  comment = "Role for data analysts"
}

resource "snowflake_role" "data_scientist" {
  name    = "DATA_SCIENTIST"
  comment = "Role for data scientists"
}

# ============================================================================
# Outputs
# ============================================================================

output "warehouse_names" {
  value = [
    snowflake_warehouse.wh_ingest.name,
    snowflake_warehouse.wh_trans.name,
    snowflake_warehouse.wh_analyt.name,
    snowflake_warehouse.wh_load.name
  ]
}

output "database_names" {
  value = [
    snowflake_database.raw_db.name,
    snowflake_database.staging_db.name,
    snowflake_database.dw_db.name
  ]
}

