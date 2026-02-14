# Staging Environment Configuration
# Similar to dev but with PRODUCTION instance type

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
  #   prefix = "staging/bigtable-pipeline"
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
  environment = "staging"
  labels = {
    environment = local.environment
    managed_by  = "terraform"
    project     = "bigtable-pipeline"
  }
}

module "bigtable" {
  source = "../../modules/bigtable"

  project_id        = var.project_id
  instance_name     = "${local.environment}-bigtable-instance"
  cluster_id        = "${local.environment}-bigtable-cluster"
  zone              = var.zone
  instance_type     = "PRODUCTION"
  num_nodes         = 3 # More nodes for staging
  display_name      = "Bigtable Instance - Staging"
  labels            = local.labels
  deletion_protection = true
}

module "networking" {
  source = "../../modules/networking"

  project_id = var.project_id
  network_name = "${local.environment}-data-pipeline-network"
  
  subnets = [
    {
      name          = "${local.environment}-subnet-${var.region}"
      ip_cidr_range = "10.1.1.0/24"
      region        = var.region
      description   = "Subnet for staging environment"
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
  value = module.bigtable.instance_name
}

output "bigtable_fact_table" {
  value = module.bigtable.fact_table_name
}

output "bigtable_aggregate_table" {
  value = module.bigtable.aggregate_table_name
}

output "network_name" {
  value = module.networking.network_name
}

output "pipeline_service_account_email" {
  value = module.service_accounts.service_account_emails["pipeline-sa"]
}
