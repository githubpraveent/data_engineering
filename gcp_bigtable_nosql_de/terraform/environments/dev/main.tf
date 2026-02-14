# Development Environment Configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Optional: Remote state backend (uncomment and configure)
  # backend "gcs" {
  #   bucket = "terraform-state-bucket"
  #   prefix = "dev/bigtable-pipeline"
  # }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "" # Set via terraform.tfvars or TF_VAR_project_id
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Zone"
  type        = string
  default     = "us-central1-a"
}

# Locals
locals {
  environment = "dev"
  labels = {
    environment = local.environment
    managed_by  = "terraform"
    project     = "bigtable-pipeline"
  }
}

# Bigtable Module
module "bigtable" {
  source = "../../modules/bigtable"

  project_id       = var.project_id
  instance_name    = "${local.environment}-bigtable-instance"
  cluster_id       = "${local.environment}-bigtable-cluster"
  zone             = var.zone
  instance_type    = "DEVELOPMENT" # Use DEVELOPMENT for dev env
  num_nodes        = 1
  display_name     = "Bigtable Instance - Development"
  labels           = local.labels
  deletion_protection = false
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_id = var.project_id
  network_name = "${local.environment}-data-pipeline-network"
  
  subnets = [
    {
      name          = "${local.environment}-subnet-${var.region}"
      ip_cidr_range = "10.0.1.0/24"
      region        = var.region
      description   = "Subnet for development environment"
    }
  ]

  labels = local.labels
}

# Service Accounts Module
module "service_accounts" {
  source = "../../modules/service-accounts"

  project_id = var.project_id

  service_accounts = {
    "pipeline-sa" = {
      display_name = "Data Pipeline Service Account"
      description  = "Service account for data pipeline operations"
      roles = [
        "roles/bigtable.user",
        "roles/bigtable.reader",
        "roles/logging.logWriter",
        "roles/monitoring.metricWriter"
      ]
    }
    "github-actions-sa" = {
      display_name = "GitHub Actions Service Account"
      description  = "Service account for GitHub Actions CI/CD"
      roles = [
        "roles/bigtable.admin",
        "roles/compute.admin",
        "roles/iam.serviceAccountUser",
        "roles/logging.logWriter"
      ]
      create_key = false # Use Workload Identity Federation instead
    }
  }

  labels = local.labels
}

# Outputs
output "bigtable_instance_name" {
  description = "Name of the Bigtable instance"
  value       = module.bigtable.instance_name
}

output "bigtable_fact_table" {
  description = "Name of the fact table"
  value       = module.bigtable.fact_table_name
}

output "bigtable_aggregate_table" {
  description = "Name of the aggregate table"
  value       = module.bigtable.aggregate_table_name
}

output "network_name" {
  description = "Name of the VPC network"
  value       = module.networking.network_name
}

output "pipeline_service_account_email" {
  description = "Email of the pipeline service account"
  value       = module.service_accounts.service_account_emails["pipeline-sa"]
}
