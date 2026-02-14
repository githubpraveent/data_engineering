variable "environment" {
  description = "Environment name"
  type        = string
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "s3_datalake_bucket_arn" {
  description = "S3 Data Lake bucket ARN"
  type        = string
}

variable "msk_cluster_arn" {
  description = "MSK cluster ARN"
  type        = string
}

variable "redshift_cluster_arn" {
  description = "Redshift cluster ARN"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

