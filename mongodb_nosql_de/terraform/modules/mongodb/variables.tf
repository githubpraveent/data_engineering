variable "environment" {
  description = "Environment name"
  type        = string
}

variable "mongodb_atlas_org_id" {
  description = "MongoDB Atlas Organization ID"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for peering"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs"
  type        = list(string)
}

variable "allowed_cidr_blocks" {
  description = "Allowed CIDR blocks for IP whitelist"
  type        = list(string)
}

variable "mongodb_cluster_tier" {
  description = "MongoDB cluster tier"
  type        = string
  default     = "M10"
}

variable "mongodb_cluster_region" {
  description = "MongoDB cluster region"
  type        = string
  default     = "US_EAST_1"
}
