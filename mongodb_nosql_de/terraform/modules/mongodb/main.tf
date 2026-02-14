/**
 * MongoDB Atlas Module
 * 
 * Provisions a MongoDB Atlas cluster with proper networking and security.
 * Configures VPC peering or private endpoints for secure connectivity.
 */

# MongoDB Atlas Project
resource "mongodbatlas_project" "main" {
  name   = "${var.project_name}-${var.environment}"
  org_id = var.mongodb_atlas_org_id

  tags = [
    {
      key   = "Environment"
      value = var.environment
    },
    {
      key   = "Project"
      value = var.project_name
    }
  ]
}

# MongoDB Atlas Cluster
resource "mongodbatlas_cluster" "main" {
  project_id   = mongodbatlas_project.main.id
  name         = "${var.project_name}-${var.environment}-cluster"
  cluster_type = "REPLICASET"

  # Provider settings
  provider_name               = "AWS"
  provider_region_name        = var.mongodb_cluster_region
  provider_instance_size_name = var.mongodb_cluster_tier

  # Backup and replication
  replication_factor = 3
  num_shards         = 1

  # Backup configuration
  provider_backup_enabled = true
  pit_enabled            = true

  # Auto-scaling
  auto_scaling_disk_gb_enabled = true

  tags = [
    {
      key   = "Environment"
      value = var.environment
    }
  ]
}

# Database User
resource "mongodbatlas_database_user" "pipeline_user" {
  username           = "pipeline_user"
  password           = random_password.mongodb_password.result
  project_id         = mongodbatlas_project.main.id
  auth_database_name = "admin"

  roles {
    role_name     = "readWrite"
    database_name = "data_pipeline"
  }

  roles {
    role_name     = "read"
    database_name = "admin"
  }

  labels {
    key   = "Environment"
    value = var.environment
  }

  scopes {
    type = "CLUSTER"
    name = mongodbatlas_cluster.main.name
  }
}

# Generate secure password
resource "random_password" "mongodb_password" {
  length  = 32
  special = true
  override_special = "!@#$%^&*()_+-="
}

# Network Peering (for private connectivity)
resource "mongodbatlas_network_container" "main" {
  project_id    = mongodbatlas_project.main.id
  atlas_cidr_block = "10.8.0.0/18"
  provider_name = "AWS"
  region_name   = var.mongodb_cluster_region
}

resource "mongodbatlas_network_peering" "main" {
  accepter_region_name   = var.mongodb_cluster_region
  project_id             = mongodbatlas_project.main.id
  container_id           = mongodbatlas_network_container.main.container_id
  provider_name          = "AWS"
  route_table_cidr_block = "10.0.0.0/16"
  vpc_id                 = var.vpc_id
  aws_account_id         = data.aws_caller_identity.current.account_id
}

data "aws_caller_identity" "current" {}

# IP Whitelist (for public access - use private endpoints in production)
resource "mongodbatlas_project_ip_access_list" "vpc" {
  project_id = mongodbatlas_project.main.id
  cidr_block = var.allowed_cidr_blocks[0]
  comment    = "VPC CIDR for ${var.environment}"
}

# Output connection string (standard format)
locals {
  cluster_srv = replace(replace(mongodbatlas_cluster.main.connection_strings[0].srv_connection_string, "mongodb+srv://", ""), "/?ssl=true", "")
  connection_string = "mongodb+srv://${mongodbatlas_database_user.pipeline_user.username}:${urlencode(mongodbatlas_database_user.pipeline_user.password)}@${local.cluster_srv}/data_pipeline?retryWrites=true&w=majority"
}
