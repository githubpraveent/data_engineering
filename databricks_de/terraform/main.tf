# Terraform configuration for Databricks retail data lakehouse infrastructure

terraform {
  required_version = ">= 1.0"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure S3 backend for state management
    bucket = "databricks-terraform-state"
    key    = "retail-datalake/terraform.tfstate"
    region = "us-east-1"
  }
}

# Provider configuration
provider "databricks" {
  host  = var.databricks_host
  token = var.databricks_token
}

provider "aws" {
  region = var.aws_region
}

# Databricks workspace configuration (if using AWS)
resource "databricks_mws_workspaces" "retail_workspace" {
  account_id      = var.databricks_account_id
  workspace_name  = "${var.environment}-retail-datalake"
  deployment_name = "${var.environment}-retail-datalake"
  aws_region      = var.aws_region

  # Network configuration
  network {
    network_id = aws_vpc.databricks_vpc.id
  }

  # Storage configuration (S3 bucket)
  storage_configuration_id = databricks_mws_storage_configurations.s3_storage.storage_configuration_id
  credentials_id           = databricks_mws_credential.aws_credentials.credentials_id

  tags = {
    Environment = var.environment
    Project     = "retail-datalake"
  }
}

# S3 Storage Configuration for Unity Catalog
resource "databricks_mws_storage_configurations" "s3_storage" {
  account_id                 = var.databricks_account_id
  bucket_name                = aws_s3_bucket.unity_catalog.bucket
  storage_configuration_name = "${var.environment}-unity-catalog-storage"
}

# AWS Credentials for Databricks
resource "databricks_mws_credential" "aws_credentials" {
  account_id       = var.databricks_account_id
  role_arn         = aws_iam_role.databricks_unity_catalog.arn
  credentials_name = "${var.environment}-databricks-credentials"
}

# S3 Bucket for Unity Catalog metastore
resource "aws_s3_bucket" "unity_catalog" {
  bucket = "${var.environment}-retail-datalake-unity-catalog-${var.aws_region}"

  tags = {
    Name        = "Unity Catalog Metastore"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "unity_catalog" {
  bucket = aws_s3_bucket.unity_catalog.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Unity Catalog Metastore
resource "databricks_mws_metastores" "metastore" {
  account_id     = var.databricks_account_id
  metastore_name = "${var.environment}-retail-metastore"
  storage_root   = "s3://${aws_s3_bucket.unity_catalog.bucket}/metastore"
  region         = var.aws_region

  depends_on = [databricks_mws_storage_configurations.s3_storage]
}

# Assign metastore to workspace
resource "databricks_mws_metastore_assignment" "metastore_assignment" {
  workspace_id         = databricks_mws_workspaces.retail_workspace.workspace_id
  metastore_id         = databricks_mws_metastores.metastore.metastore_id
  default_catalog_name = "retail_datalake"
}

# Unity Catalog Catalogs (Bronze, Silver, Gold)
resource "databricks_catalog" "retail_catalog" {
  name         = "retail_datalake"
  storage_root = "s3://${aws_s3_bucket.unity_catalog.bucket}/catalogs/retail_datalake"
  comment      = "Retail Data Lakehouse Catalog"

  depends_on = [databricks_mws_metastore_assignment.metastore_assignment]
}

# Unity Catalog Schemas
resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.retail_catalog.name
  name         = "${var.environment}_bronze"
  comment      = "Bronze layer: Raw/ingested data"
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.retail_catalog.name
  name         = "${var.environment}_silver"
  comment      = "Silver layer: Cleaned/refined data"
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.retail_catalog.name
  name         = "${var.environment}_gold"
  comment      = "Gold layer: Business-level tables"
}

resource "databricks_schema" "monitoring" {
  catalog_name = databricks_catalog.retail_catalog.name
  name         = "${var.environment}_monitoring"
  comment      = "Monitoring and metrics tables"
}

# Databricks Cluster for Jobs (compute optimized)
resource "databricks_cluster" "job_cluster" {
  cluster_name            = "${var.environment}-job-cluster"
  spark_version           = "13.3.x-scala2.12"
  node_type_id            = var.node_type_id
  driver_node_type_id     = var.node_type_id
  num_workers             = var.num_workers
  autotermination_minutes = 30

  spark_conf = {
    "spark.databricks.delta.optimizeWrite.enabled" = "true"
    "spark.databricks.delta.autoCompact.enabled"   = "true"
    "spark.sql.adaptive.enabled"                   = "true"
    "spark.sql.adaptive.coalescePartitions.enabled" = "true"
  }

  cluster_log_conf {
    s3 {
      destination = "s3://${aws_s3_bucket.cluster_logs.bucket}/cluster-logs"
    }
  }

  aws_attributes {
    first_on_demand       = 1
    availability          = "SPOT_WITH_FALLBACK"
    zone_id               = var.aws_zone_id
    spot_bid_price_percent = 100
    ebs_volume_type       = "GENERAL_PURPOSE_SSD"
    ebs_volume_count      = 2
    ebs_volume_size       = 100
  }

  tags = {
    Environment = var.environment
    Purpose     = "Jobs"
  }
}

# Databricks SQL Warehouse (for analytics)
resource "databricks_sql_endpoint" "analytics_warehouse" {
  name             = "${var.environment}-analytics-warehouse"
  cluster_size     = "Small"
  min_num_clusters = 1
  max_num_clusters = 3
  auto_stop_mins   = 10
  enable_photon    = true
  enable_serverless_compute = true

  tags = {
    Environment = var.environment
    Purpose     = "Analytics"
  }
}

# S3 Bucket for cluster logs
resource "aws_s3_bucket" "cluster_logs" {
  bucket = "${var.environment}-retail-datalake-cluster-logs-${var.aws_region}"

  tags = {
    Name        = "Databricks Cluster Logs"
    Environment = var.environment
  }
}

# IAM Role for Databricks Unity Catalog
resource "aws_iam_role" "databricks_unity_catalog" {
  name = "${var.environment}-databricks-unity-catalog-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = var.databricks_account_arn
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Environment = var.environment
  }
}

# IAM Policy for Unity Catalog access
resource "aws_iam_role_policy" "databricks_unity_catalog" {
  name = "${var.environment}-databricks-unity-catalog-policy"
  role = aws_iam_role.databricks_unity_catalog.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.unity_catalog.arn,
          "${aws_s3_bucket.unity_catalog.arn}/*"
        ]
      }
    ]
  })
}

# VPC Configuration (if using VPC)
resource "aws_vpc" "databricks_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.environment}-databricks-vpc"
  }
}

resource "aws_subnet" "databricks_private" {
  vpc_id            = aws_vpc.databricks_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = var.aws_zone_id

  tags = {
    Name = "${var.environment}-databricks-private-subnet"
  }
}

resource "aws_subnet" "databricks_public" {
  vpc_id            = aws_vpc.databricks_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = var.aws_zone_id

  tags = {
    Name = "${var.environment}-databricks-public-subnet"
  }
}

# Outputs
output "workspace_url" {
  value       = databricks_mws_workspaces.retail_workspace.workspace_url
  description = "Databricks workspace URL"
}

output "metastore_id" {
  value       = databricks_mws_metastores.metastore.metastore_id
  description = "Unity Catalog metastore ID"
}

output "sql_warehouse_id" {
  value       = databricks_sql_endpoint.analytics_warehouse.id
  description = "SQL Warehouse ID"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.unity_catalog.bucket
  description = "S3 bucket for Unity Catalog"
}

