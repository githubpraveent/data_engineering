variable "environment" {
  description = "Environment name"
  type        = string
}

variable "glue_service_role_arn" {
  description = "Glue service role ARN"
  type        = string
}

variable "s3_datalake_bucket" {
  description = "S3 Data Lake bucket name"
  type        = string
}

variable "msk_bootstrap_servers" {
  description = "MSK bootstrap broker addresses"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

