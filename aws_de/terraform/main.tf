terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure backend in environments/{env}/backend.tf
    # bucket = "terraform-state-{env}"
    # key    = "retail-datalake/terraform.tfstate"
    # region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "retail-datalake"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  environment          = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = slice(data.aws_availability_zones.available.names, 0, 3)
  enable_nat_gateway  = true
  enable_vpn_gateway  = false
  single_nat_gateway  = var.environment != "prod" # Cost optimization for non-prod

  tags = local.common_tags
}

# S3 Data Lake Module
module "s3_datalake" {
  source = "./modules/s3"

  environment = var.environment
  account_id  = data.aws_caller_identity.current.account_id

  tags = local.common_tags
}

# MSK Module
module "msk" {
  source = "./modules/msk"

  environment           = var.environment
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnet_ids
  security_group_ids   = [module.vpc.msk_security_group_id]
  kafka_version        = var.msk_kafka_version
  instance_type        = var.msk_instance_type
  broker_count         = var.msk_broker_count
  storage_size         = var.msk_storage_size

  tags = local.common_tags
}

# IAM Roles Module
module "iam" {
  source = "./modules/iam"

  environment = var.environment
  account_id  = data.aws_caller_identity.current.account_id

  s3_datalake_bucket_arn = module.s3_datalake.bucket_arn
  msk_cluster_arn        = module.msk.cluster_arn
  redshift_cluster_arn   = module.redshift.cluster_arn

  tags = local.common_tags
}

# Glue Module
module "glue" {
  source = "./modules/glue"

  environment = var.environment

  glue_service_role_arn = module.iam.glue_service_role_arn
  s3_datalake_bucket    = module.s3_datalake.bucket_name
  msk_bootstrap_servers = module.msk.bootstrap_brokers

  tags = local.common_tags
}

# Redshift Module
module "redshift" {
  source = "./modules/redshift"

  environment = var.environment

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  security_group_ids = [module.vpc.redshift_security_group_id]

  node_type          = var.redshift_node_type
  number_of_nodes    = var.redshift_number_of_nodes
  database_name      = var.redshift_database_name
  master_username    = var.redshift_master_username
  master_password    = var.redshift_master_password # Use AWS Secrets Manager in production

  s3_datalake_bucket = module.s3_datalake.bucket_name
  redshift_role_arn  = module.iam.redshift_role_arn

  tags = local.common_tags
}

# CloudWatch Alarms
module "monitoring" {
  source = "./modules/monitoring"

  environment = var.environment

  msk_cluster_name    = module.msk.cluster_name
  glue_job_names      = module.glue.job_names
  redshift_cluster_id = module.redshift.cluster_id

  tags = local.common_tags
}

