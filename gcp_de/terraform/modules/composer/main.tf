# Cloud Composer (Airflow) Module
# Creates managed Airflow environment

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
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

variable "node_count" {
  description = "Number of nodes in the Composer environment"
  type        = number
  default     = 3
}

variable "machine_type" {
  description = "Machine type for Composer nodes"
  type        = string
  default     = "n1-standard-1"
}

variable "disk_size_gb" {
  description = "Disk size in GB for Composer nodes"
  type        = number
  default     = 30
}

variable "airflow_config_overrides" {
  description = "Airflow configuration overrides"
  type        = map(string)
  default = {
    "core-dags_are_paused_at_creation" = "True"
    "core-max_active_runs_per_dag"      = "3"
    "scheduler-dag_dir_list_interval"   = "300"
  }
}

variable "env_variables" {
  description = "Environment variables for Airflow"
  type        = map(string)
  default = {
    ENVIRONMENT = "dev"
  }
}

variable "dags_bucket_name" {
  description = "Name of the GCS bucket for Airflow DAGs"
  type        = string
}

variable "dataflow_staging_bucket_name" {
  description = "Name of the GCS bucket for Dataflow staging"
  type        = string
}

variable "dataflow_temp_bucket_name" {
  description = "Name of the GCS bucket for Dataflow temp"
  type        = string
}

variable "raw_bucket_name" {
  description = "Name of the raw zone GCS bucket"
  type        = string
}

variable "staging_bucket_name" {
  description = "Name of the staging zone GCS bucket"
  type        = string
}

variable "curated_bucket_name" {
  description = "Name of the curated zone GCS bucket"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Composer"
  type        = string
  default     = ""
}

# Create Composer Environment
resource "google_composer_environment" "composer" {
  name    = "composer-${var.environment}"
  project = var.project_id
  region  = var.region

  config {
    node_count = var.node_count

    node_config {
      zone            = var.zone
      machine_type    = var.machine_type
      disk_size_gb    = var.disk_size_gb
      service_account = var.service_account_email != "" ? var.service_account_email : null
    }

    software_config {
      image_version = "composer-2-airflow-2"
      
      airflow_config_overrides = merge(
        var.airflow_config_overrides,
        {
          "core-environment" = var.environment
        }
      )

      env_variables = merge(
        var.env_variables,
        {
          GCP_PROJECT          = var.project_id
          DAGS_BUCKET          = var.dags_bucket_name
          DATAFLOW_STAGING     = var.dataflow_staging_bucket_name
          DATAFLOW_TEMP        = var.dataflow_temp_bucket_name
          RAW_BUCKET           = var.raw_bucket_name
          STAGING_BUCKET       = var.staging_bucket_name
          CURATED_BUCKET       = var.curated_bucket_name
        }
      )

      pypi_packages = {
        "apache-beam[gcp]" = "2.50.0"
        "google-cloud-bigquery" = "3.11.0"
        "google-cloud-storage" = "2.10.0"
        "google-cloud-pubsub" = "2.18.0"
      }
    }
  }

  labels = {
    environment = var.environment
    purpose     = "data-orchestration"
  }
}

# Outputs
output "composer_environment_name" {
  value       = google_composer_environment.composer.name
  description = "Name of the Composer environment"
}

output "airflow_uri" {
  value       = google_composer_environment.composer.config[0].airflow_uri
  description = "URI of the Airflow web server"
}

output "gke_cluster" {
  value       = google_composer_environment.composer.config[0].gke_cluster
  description = "GKE cluster name"
}

