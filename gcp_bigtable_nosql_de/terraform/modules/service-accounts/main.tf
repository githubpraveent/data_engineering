# Service Accounts Module
# Creates service accounts with least privilege IAM roles

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

variable "service_accounts" {
  description = "Map of service accounts to create"
  type = map(object({
    display_name = string
    description  = string
    roles        = list(string)
  }))
  default = {}
}

variable "labels" {
  description = "Labels to apply to service accounts"
  type        = map(string)
  default     = {}
}

# Service Accounts
resource "google_service_account" "accounts" {
  for_each = var.service_accounts

  account_id   = each.key
  project      = var.project_id
  display_name = each.value.display_name
  description  = each.value.description
  labels       = var.labels
}

# IAM Role Bindings
resource "google_project_iam_member" "role_bindings" {
  for_each = {
    for sa_role in flatten([
      for sa_name, sa_config in var.service_accounts : [
        for role in sa_config.roles : {
          key          = "${sa_name}-${role}"
          sa_email     = google_service_account.accounts[sa_name].email
          role         = role
          member       = "serviceAccount:${google_service_account.accounts[sa_name].email}"
        }
      ]
    ]) : sa_role.key => sa_role
  }

  project = var.project_id
  role    = each.value.role
  member  = each.value.member
}

# Service Account Keys (optional - for GitHub Actions)
# WARNING: Only create keys if absolutely necessary. Prefer workload identity federation.
resource "google_service_account_key" "keys" {
  for_each = {
    for sa_name, sa_config in var.service_accounts : sa_name => sa_config
    if try(sa_config.create_key, false) == true
  }

  service_account_id = google_service_account.accounts[each.key].name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Outputs
output "service_account_emails" {
  description = "Email addresses of created service accounts"
  value = {
    for sa_name, sa in google_service_account.accounts : sa_name => sa.email
  }
}

output "service_account_names" {
  description = "Full names of created service accounts"
  value = {
    for sa_name, sa in google_service_account.accounts : sa_name => sa.name
  }
}

output "service_account_keys" {
  description = "Service account keys (base64 encoded). Use only if keys were created."
  value = {
    for sa_name, key in google_service_account_key.keys : sa_name => key.private_key
  }
  sensitive = true
}
