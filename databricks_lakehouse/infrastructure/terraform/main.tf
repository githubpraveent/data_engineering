# Terraform configuration for Databricks Lakehouse infrastructure
# Adjust provider and resource details based on your cloud provider

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
}

provider "databricks" {
  host  = var.databricks_workspace_url
  token = var.databricks_token
}

provider "aws" {
  region = var.aws_region
}

# Databricks Cluster for Streaming
resource "databricks_cluster" "streaming_cluster" {
  cluster_name            = "lakehouse-streaming-cluster"
  spark_version           = "14.3.x-scala2.12"
  node_type_id            = var.streaming_node_type
  driver_node_type_id     = var.streaming_node_type
  num_workers              = var.streaming_num_workers
  autotermination_minutes = 30
  enable_elastic_disk      = true

  spark_conf = {
    "spark.databricks.delta.optimizeWrite.enabled"     = "true"
    "spark.databricks.delta.autoCompact.enabled"        = "true"
    "spark.databricks.delta.autoCompact.targetFileSize" = "128MB"
    "spark.sql.streaming.checkpointLocation"            = "${var.checkpoint_root}"
    "spark.sql.adaptive.enabled"                        = "true"
    "spark.sql.adaptive.coalescePartitions.enabled"     = "true"
    "spark.sql.adaptive.skewJoin.enabled"               = "true"
    "spark.sql.adaptive.localShuffleReader.enabled"     = "true"
    "spark.sql.adaptive.advisoryPartitionSizeInBytes"   = "64MB"
    "spark.databricks.io.cache.enabled"                 = "true"
    "spark.databricks.io.cache.maxDiskUsage"           = "50g"
    "spark.databricks.io.cache.maxMetaDataCache"        = "1g"
    "spark.sql.optimizer.dynamicPartitionPruning.enabled" = "true"
    "spark.sql.optimizer.dynamicPartitionPruning.useStats" = "true"
    "spark.sql.shuffle.partitions"                      = "200"
    "spark.sql.autoBroadcastJoinThreshold"              = "50MB"
    "spark.sql.execution.arrow.pyspark.enabled"        = "true"
    "spark.memory.fraction"                             = "0.8"
    "spark.memory.storageFraction"                      = "0.3"
  }

  library {
    maven {
      coordinates = "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0"
    }
  }

  custom_tags = {
    ResourceClass = "Streaming"
    Environment   = var.environment
  }
}

# Databricks Cluster for ML
resource "databricks_cluster" "ml_cluster" {
  cluster_name            = "lakehouse-ml-cluster"
  spark_version           = "14.3.x-scala2.12"
  node_type_id            = var.ml_node_type
  driver_node_type_id     = var.ml_node_type
  num_workers              = var.ml_num_workers
  autotermination_minutes = 30

  spark_conf = {
    "spark.databricks.mlflow.trackingUri"              = "databricks"
    "spark.sql.adaptive.enabled"                        = "true"
    "spark.sql.adaptive.coalescePartitions.enabled"     = "true"
    "spark.databricks.delta.optimizeWrite.enabled"     = "true"
    "spark.databricks.io.cache.enabled"                 = "true"
    "spark.sql.shuffle.partitions"                      = "200"
    "spark.sql.autoBroadcastJoinThreshold"              = "50MB"
  }

  custom_tags = {
    ResourceClass = "ML"
    Environment   = var.environment
  }
}

# Unity Catalog
resource "databricks_catalog" "lakehouse" {
  name    = "lakehouse"
  comment = "Main production catalog for lakehouse"
}

resource "databricks_schema" "bronze" {
  catalog_name = databricks_catalog.lakehouse.name
  name         = "bronze"
  comment      = "Bronze layer: Raw ingested data"
}

resource "databricks_schema" "silver" {
  catalog_name = databricks_catalog.lakehouse.name
  name         = "silver"
  comment      = "Silver layer: Cleaned and enriched data"
}

resource "databricks_schema" "gold" {
  catalog_name = databricks_catalog.lakehouse.name
  name         = "gold"
  comment      = "Gold layer: Analytics-ready aggregated data"
}

# S3 Bucket for Delta Lake storage (if using AWS)
resource "aws_s3_bucket" "lakehouse_data" {
  bucket = var.s3_bucket_name

  tags = {
    Name        = "Databricks Lakehouse Data"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "lakehouse_data" {
  bucket = aws_s3_bucket.lakehouse_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# IAM Role for Databricks to access S3
resource "aws_iam_role" "databricks_access" {
  name = "databricks-lakehouse-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "databricks_s3_access" {
  name = "databricks-s3-access-policy"
  role = aws_iam_role.databricks_access.id

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
          "${aws_s3_bucket.lakehouse_data.arn}/*",
          aws_s3_bucket.lakehouse_data.arn
        ]
      }
    ]
  })
}
