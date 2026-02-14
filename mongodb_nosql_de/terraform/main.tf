/**
 * Main Terraform Configuration
 * 
 * This file sets up the core infrastructure for the MongoDB Data Engineering Pipeline.
 * It orchestrates VPC, compute, MongoDB Atlas cluster, and monitoring resources.
 */

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.0"
    }
  }

  # Backend configuration (configure based on your setup)
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "mongodb-pipeline/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "MongoDB-Data-Pipeline"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Configure MongoDB Atlas Provider
provider "mongodbatlas" {
  public_key  = var.mongodb_atlas_api_key
  private_key = var.mongodb_atlas_api_secret
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
  project_name       = var.project_name
}

# MongoDB Atlas Module
module "mongodb" {
  source = "./modules/mongodb"

  environment          = var.environment
  mongodb_atlas_org_id = var.mongodb_atlas_org_id
  project_name         = var.project_name
  aws_region           = var.aws_region
  vpc_id               = module.vpc.vpc_id
  private_subnet_ids   = module.vpc.private_subnet_ids
  allowed_cidr_blocks  = [var.vpc_cidr]
}

# Compute Module
module "compute" {
  source = "./modules/compute"

  environment       = var.environment
  project_name      = var.project_name
  vpc_id            = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  security_group_id = module.vpc.security_group_id

  instance_type     = var.instance_type
  key_pair_name     = var.key_pair_name
  mongodb_uri       = module.mongodb.connection_string

  depends_on = [module.mongodb]
}

# Monitoring Module
module "monitoring" {
  source = "./modules/monitoring"

  environment  = var.environment
  project_name = var.project_name

  pipeline_function_name = module.compute.pipeline_function_name
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "mongodb_connection_string" {
  description = "MongoDB Atlas connection string"
  value       = module.mongodb.connection_string
  sensitive   = true
}

output "mongodb_cluster_name" {
  description = "MongoDB cluster name"
  value       = module.mongodb.cluster_name
}

output "ec2_instance_ips" {
  description = "EC2 instance public IPs"
  value       = module.compute.instance_public_ips
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch Dashboard URL"
  value       = module.monitoring.dashboard_url
}
