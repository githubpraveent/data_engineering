# Production Environment Configuration
# Similar to staging but with stricter settings

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # backend "gcs" {
  #   bucket = "terraform-state-bucket"
  #   prefix = "production/bigtable-pipeline"
  # }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = ""
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

locals {
  environment = "production"
  labels = {
    environment = local.environment
    managed_by  = "terraform"
    project     = "bigtable-pipeline"
    critical    = "true"
  }
}

module "bigtable" {
  source = "../../modules/bigtable"

  project_id        = var.project_id
  instance_name     = "${local.environment}-bigtable-instance"
  cluster_id        = "${local.environment}-bigtable-cluster"
  zone              = var.zone
  instance_type     = "PRODUCTION"
  num_nodes         = 5 # More nodes for production
  display_name      = "Bigtable Instance - Production"
  labels            = local.labels
  deletion_protection = true # Always enabled for production
}

module "networking" {
  source = "../../modules/networking"

  project_id = var.project_id
  network_name = "${local.environment}-data-pipeline-network"
  
  subnets = [
    {
      name          = "${local.environment}-subnet-${var.region}"
      ip_cidr_range = "10.2.1.0/24"
      region        = var.region
      description   = "Subnet for production environment"
    }
  ]

  labels = local.labels
}

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
      create_key = false
    }
  }

  labels = local.labels
}

output "bigtable_instance_name" {
  value       = module.bigtable.instance_name
  description = "Name of the Bigtable instance"
}

output "bigtable_fact_table" {
  value       = module.bigtable.fact_table_name
  description = "Name of the fact table"
}

output "bigtable_aggregate_table" {
  value       = module.bigtable.aggregate_table_name
  description = "Name of the aggregate table"
}

output "network_name" {
  value       = module.networking.network_name
  description = "Name of the VPC network"
}

output "pipeline_service_account_email" {
  value       = module.service_accounts.service_account_emails["pipeline-sa"]
  description = "Email of the pipeline service account"
}
