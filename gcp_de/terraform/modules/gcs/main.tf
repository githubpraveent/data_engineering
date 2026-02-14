# GCS Buckets Module
# Creates data lake buckets for raw, staging, and curated zones

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

variable "enable_versioning" {
  description = "Enable object versioning for buckets"
  type        = bool
  default     = true
}

variable "raw_retention_days" {
  description = "Number of days to retain raw zone data"
  type        = number
  default     = 90
}

variable "staging_retention_days" {
  description = "Number of days to retain staging zone data"
  type        = number
  default     = 180
}

variable "curated_retention_days" {
  description = "Number of days to retain curated zone data"
  type        = number
  default     = 2555  # 7 years
}

locals {
  bucket_prefix = "${var.project_id}-data-lake"
}

# Raw Zone Bucket (Bronze)
resource "google_storage_bucket" "raw" {
  name          = "${local.bucket_prefix}-raw-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    condition {
      age = var.raw_retention_days
    }
    action {
      type = "Delete"
    }
  }

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    zone        = "raw"
    purpose     = "data-lake"
  }
}

# Staging Zone Bucket (Silver)
resource "google_storage_bucket" "staging" {
  name          = "${local.bucket_prefix}-staging-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    condition {
      age = var.staging_retention_days
    }
    action {
      type = "Delete"
    }
  }

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    zone        = "staging"
    purpose     = "data-lake"
  }
}

# Curated Zone Bucket (Gold)
resource "google_storage_bucket" "curated" {
  name          = "${local.bucket_prefix}-curated-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  versioning {
    enabled = var.enable_versioning
  }

  lifecycle_rule {
    condition {
      age = 365  # After 1 year, move to Coldline
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = var.curated_retention_days
    }
    action {
      type = "Delete"
    }
  }

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    zone        = "curated"
    purpose     = "data-lake"
  }
}

# Airflow DAGs Bucket (for Cloud Composer)
resource "google_storage_bucket" "airflow_dags" {
  name          = "${var.project_id}-composer-dags-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "airflow-dags"
  }
}

# Dataflow Staging Bucket
resource "google_storage_bucket" "dataflow_staging" {
  name          = "${var.project_id}-dataflow-staging-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "dataflow-staging"
  }
}

# Dataflow Temp Bucket
resource "google_storage_bucket" "dataflow_temp" {
  name          = "${var.project_id}-dataflow-temp-${var.environment}"
  location      = var.region
  project       = var.project_id
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  labels = {
    environment = var.environment
    purpose     = "dataflow-temp"
  }
}

# Outputs
output "raw_bucket_name" {
  value       = google_storage_bucket.raw.name
  description = "Name of the raw zone bucket"
}

output "staging_bucket_name" {
  value       = google_storage_bucket.staging.name
  description = "Name of the staging zone bucket"
}

output "curated_bucket_name" {
  value       = google_storage_bucket.curated.name
  description = "Name of the curated zone bucket"
}

output "airflow_dags_bucket_name" {
  value       = google_storage_bucket.airflow_dags.name
  description = "Name of the Airflow DAGs bucket"
}

output "dataflow_staging_bucket_name" {
  value       = google_storage_bucket.dataflow_staging.name
  description = "Name of the Dataflow staging bucket"
}

output "dataflow_temp_bucket_name" {
  value       = google_storage_bucket.dataflow_temp.name
  description = "Name of the Dataflow temp bucket"
}

