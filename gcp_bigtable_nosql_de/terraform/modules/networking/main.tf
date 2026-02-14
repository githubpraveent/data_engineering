# Networking Module
# Provisions VPC, subnets, and firewall rules for the data pipeline

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

variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "data-pipeline-network"
}

variable "auto_create_subnetworks" {
  description = "Whether to create subnetworks automatically"
  type        = bool
  default     = false
}

variable "routing_mode" {
  description = "The network-wide routing mode to use"
  type        = string
  default     = "GLOBAL"
}

variable "subnets" {
  description = "List of subnetworks to create"
  type = list(object({
    name          = string
    ip_cidr_range = string
    region        = string
    description   = string
  }))
  default = []
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}

# VPC Network
resource "google_compute_network" "vpc" {
  name                    = var.network_name
  project                 = var.project_id
  auto_create_subnetworks = var.auto_create_subnetworks
  routing_mode            = var.routing_mode
  labels                  = var.labels
}

# Subnetworks
resource "google_compute_subnetwork" "subnets" {
  for_each = {
    for subnet in var.subnets : subnet.name => subnet
  }

  name          = each.value.name
  project       = var.project_id
  ip_cidr_range = each.value.ip_cidr_range
  region        = each.value.region
  network       = google_compute_network.vpc.id
  description   = each.value.description
  labels        = var.labels
}

# Firewall Rules
# Allow internal traffic within the VPC
resource "google_compute_firewall" "allow_internal" {
  name    = "${var.network_name}-allow-internal"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "icmp"
  }

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  source_ranges = [
    for subnet in var.subnets : subnet.ip_cidr_range
  ]

  description = "Allow all internal traffic within VPC"
  labels      = var.labels
}

# Allow SSH from specific IP ranges (adjust as needed)
resource "google_compute_firewall" "allow_ssh" {
  name    = "${var.network_name}-allow-ssh"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"] # Restrict this in production!
  target_tags   = ["ssh-enabled"]

  description = "Allow SSH access"
  labels      = var.labels
}

# Allow Bigtable access (for applications running in the VPC)
resource "google_compute_firewall" "allow_bigtable" {
  name    = "${var.network_name}-allow-bigtable"
  project = var.project_id
  network = google_compute_network.vpc.name

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = [
    for subnet in var.subnets : subnet.ip_cidr_range
  ]
  target_tags = ["bigtable-client"]

  description = "Allow Bigtable API access"
  labels      = var.labels
}

# Outputs
output "network_name" {
  description = "Name of the VPC network"
  value       = google_compute_network.vpc.name
}

output "network_id" {
  description = "ID of the VPC network"
  value       = google_compute_network.vpc.id
}

output "network_self_link" {
  description = "Self link of the VPC network"
  value       = google_compute_network.vpc.self_link
}

output "subnet_names" {
  description = "Names of created subnetworks"
  value       = [for subnet in google_compute_subnetwork.subnets : subnet.name]
}

output "subnet_self_links" {
  description = "Self links of created subnetworks"
  value = {
    for k, subnet in google_compute_subnetwork.subnets : k => subnet.self_link
  }
}
