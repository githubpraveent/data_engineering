# IAM Module
# Creates service accounts and IAM bindings for data pipeline components

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
}

variable "service_accounts" {
  description = "Map of service account names to their configurations"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
  }))
  default = {
    dataflow = {
      display_name = "Dataflow Service Account"
      description  = "Service account for Dataflow jobs"
      roles = [
        "roles/dataflow.worker",
        "roles/storage.admin",
        "roles/bigquery.dataEditor",
        "roles/bigquery.jobUser",
        "roles/pubsub.subscriber",
        "roles/pubsub.publisher"
      ]
    }
    composer = {
      display_name = "Composer Service Account"
      description  = "Service account for Cloud Composer"
      roles = [
        "roles/composer.worker",
        "roles/storage.admin",
        "roles/bigquery.dataEditor",
        "roles/bigquery.jobUser",
        "roles/dataflow.developer",
        "roles/pubsub.subscriber",
        "roles/pubsub.publisher"
      ]
    }
  }
}

# Create Service Accounts
resource "google_service_account" "service_accounts" {
  for_each = var.service_accounts

  account_id   = "${each.key}-${var.environment}"
  display_name = each.value.display_name
  description  = each.value.description
  project      = var.project_id
}

# Grant IAM Roles to Service Accounts
resource "google_project_iam_member" "service_account_roles" {
  for_each = {
    for pair in flatten([
      for sa_name, sa_config in var.service_accounts : [
        for role in sa_config.roles : {
          key  = "${sa_name}-${role}"
          sa   = sa_name
          role = role
        }
      ]
    ]) : pair.key => pair
  }

  project = var.project_id
  role    = each.value.role
  member  = "serviceAccount:${google_service_account.service_accounts[each.value.sa].email}"
}

# Outputs
output "service_account_emails" {
  value       = { for k, v in google_service_account.service_accounts : k => v.email }
  description = "Map of service account keys to email addresses"
}

output "service_account_names" {
  value       = { for k, v in google_service_account.service_accounts : k => v.name }
  description = "Map of service account keys to names"
}

