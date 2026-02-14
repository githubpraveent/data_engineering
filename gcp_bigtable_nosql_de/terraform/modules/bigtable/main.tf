# Bigtable Module
# Provisions Google Bigtable instance and tables for the data pipeline

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "instance_name" {
  description = "Name of the Bigtable instance"
  type        = string
}

variable "cluster_id" {
  description = "ID of the Bigtable cluster"
  type        = string
  default     = "bigtable-cluster"
}

variable "zone" {
  description = "Zone for the Bigtable cluster"
  type        = string
  default     = "us-central1-a"
}

variable "num_nodes" {
  description = "Number of nodes in the cluster"
  type        = number
  default     = 1
}

variable "instance_type" {
  description = "Instance type: DEVELOPMENT or PRODUCTION"
  type        = string
  default     = "DEVELOPMENT"
  validation {
    condition     = contains(["DEVELOPMENT", "PRODUCTION"], var.instance_type)
    error_message = "Instance type must be DEVELOPMENT or PRODUCTION."
  }
}

variable "display_name" {
  description = "Human-readable display name for the instance"
  type        = string
  default     = ""
}

variable "labels" {
  description = "Labels to apply to the instance"
  type        = map(string)
  default     = {}
}

variable "deletion_protection" {
  description = "Whether or not to allow Terraform to destroy the instance"
  type        = bool
  default     = false
}

# Bigtable Instance
resource "google_bigtable_instance" "instance" {
  name                = var.instance_name
  project             = var.project_id
  deletion_protection = var.deletion_protection
  display_name        = var.display_name != "" ? var.display_name : var.instance_name
  instance_type       = var.instance_type
  labels              = var.labels

  cluster {
    cluster_id   = var.cluster_id
    zone         = var.zone
    num_nodes    = var.instance_type == "PRODUCTION" ? var.num_nodes : null
    storage_type = "SSD"
  }
}

# Fact Table - stores raw event data
resource "google_bigtable_table" "fact_table" {
  name          = "events_fact"
  instance_name = google_bigtable_instance.instance.name
  project       = var.project_id

  column_family {
    family = "event_data"
  }

  column_family {
    family = "metadata"
  }

  column_family {
    family = "quality"
  }
}

# Aggregate Table - stores pre-computed aggregations
resource "google_bigtable_table" "aggregate_table" {
  name          = "events_aggregate"
  instance_name = google_bigtable_instance.instance.name
  project       = var.project_id

  column_family {
    family = "daily_stats"
  }

  column_family {
    family = "weekly_stats"
  }

  column_family {
    family = "hourly_stats"
  }

  column_family {
    family = "metadata"
  }
}

# Outputs
output "instance_name" {
  description = "Name of the Bigtable instance"
  value       = google_bigtable_instance.instance.name
}

output "instance_id" {
  description = "ID of the Bigtable instance"
  value       = google_bigtable_instance.instance.id
}

output "fact_table_name" {
  description = "Name of the fact table"
  value       = google_bigtable_table.fact_table.name
}

output "aggregate_table_name" {
  description = "Name of the aggregate table"
  value       = google_bigtable_table.aggregate_table.name
}
