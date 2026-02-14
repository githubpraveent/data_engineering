# BigQuery Module
# Creates datasets and initial tables for data warehouse

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
}

variable "region" {
  description = "GCP Region for BigQuery datasets"
  type        = string
  default     = "US"
}

variable "datasets" {
  description = "Map of dataset names to their configurations"
  type = map(object({
    description      = string
    location         = string
    default_table_expiration_ms = number
    labels           = map(string)
  }))
  default = {
    staging = {
      description      = "Staging dataset for raw and lightly transformed data"
      location         = "US"
      default_table_expiration_ms = 7776000000  # 90 days
      labels = {
        purpose = "staging"
      }
    }
    curated = {
      description      = "Curated dataset for clean, modeled data"
      location         = "US"
      default_table_expiration_ms = null  # No expiration for curated data
      labels = {
        purpose = "curated"
      }
    }
    analytics = {
      description      = "Analytics dataset for aggregated and reporting tables"
      location         = "US"
      default_table_expiration_ms = null
      labels = {
        purpose = "analytics"
      }
    }
  }
}

# Create Datasets
resource "google_bigquery_dataset" "datasets" {
  for_each = var.datasets

  dataset_id                  = "${each.key}_${var.environment}"
  project                     = var.project_id
  location                    = each.value.location
  description                 = each.value.description
  default_table_expiration_ms = each.value.default_table_expiration_ms
  delete_contents_on_destroy  = var.environment != "prod"

  labels = merge(
    each.value.labels,
    {
      environment = var.environment
    }
  )

  access {
    role          = "OWNER"
    special_group = "projectOwners"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }
}

# Outputs
output "dataset_ids" {
  value       = { for k, v in google_bigquery_dataset.datasets : k => v.dataset_id }
  description = "Map of dataset keys to dataset IDs"
}

output "dataset_locations" {
  value       = { for k, v in google_bigquery_dataset.datasets : k => v.location }
  description = "Map of dataset keys to dataset locations"
}

