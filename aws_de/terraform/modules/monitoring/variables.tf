variable "environment" {
  description = "Environment name"
  type        = string
}

variable "msk_cluster_name" {
  description = "MSK cluster name"
  type        = string
}

variable "glue_job_names" {
  description = "List of Glue job names"
  type        = list(string)
}

variable "redshift_cluster_id" {
  description = "Redshift cluster identifier"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

