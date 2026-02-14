# QA Environment Configuration

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }

  backend "gcs" {
    bucket = "terraform-state-qa"  # Update with your state bucket
    prefix = "terraform/qa"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID for QA"
  type        = string
  default     = "your-qa-project-id"  # Update with your project ID
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "qa"
}

module "gcs" {
  source = "../../modules/gcs"

  project_id  = var.project_id
  environment = var.environment
  region      = var.region

  raw_retention_days      = 60
  staging_retention_days   = 120
  curated_retention_days   = 1825  # 5 years
  enable_versioning       = true
}

module "pubsub" {
  source = "../../modules/pubsub"

  project_id  = var.project_id
  environment = var.environment
}

module "bigquery" {
  source = "../../modules/bigquery"

  project_id  = var.project_id
  environment = var.environment
  region      = "US"
}

module "iam" {
  source = "../../modules/iam"

  project_id  = var.project_id
  environment = var.environment
}

module "composer" {
  source = "../../modules/composer"

  project_id  = var.project_id
  environment = var.environment
  region      = var.region

  node_count   = 2
  machine_type = "n1-standard-2"

  dags_bucket_name           = module.gcs.airflow_dags_bucket_name
  dataflow_staging_bucket_name = module.gcs.dataflow_staging_bucket_name
  dataflow_temp_bucket_name    = module.gcs.dataflow_temp_bucket_name
  raw_bucket_name             = module.gcs.raw_bucket_name
  staging_bucket_name         = module.gcs.staging_bucket_name
  curated_bucket_name         = module.gcs.curated_bucket_name

  service_account_email = module.iam.service_account_emails["composer"]
}

output "raw_bucket" {
  value = module.gcs.raw_bucket_name
}

output "staging_bucket" {
  value = module.gcs.staging_bucket_name
}

output "curated_bucket" {
  value = module.gcs.curated_bucket_name
}

output "pubsub_topics" {
  value = module.pubsub.topic_names
}

output "bigquery_datasets" {
  value = module.bigquery.dataset_ids
}

output "composer_airflow_uri" {
  value = module.composer.airflow_uri
}

output "service_accounts" {
  value = module.iam.service_account_emails
}

