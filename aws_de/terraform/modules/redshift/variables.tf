variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs for Redshift"
  type        = list(string)
}

variable "security_group_ids" {
  description = "Security group IDs for Redshift"
  type        = list(string)
}

variable "node_type" {
  description = "Redshift node type"
  type        = string
  default     = "dc2.large"
}

variable "number_of_nodes" {
  description = "Number of Redshift nodes"
  type        = number
  default     = 2
}

variable "database_name" {
  description = "Redshift database name"
  type        = string
  default     = "retail_dw"
}

variable "master_username" {
  description = "Redshift master username"
  type        = string
  sensitive   = true
}

variable "master_password" {
  description = "Redshift master password"
  type        = string
  sensitive   = true
}

variable "s3_datalake_bucket" {
  description = "S3 Data Lake bucket name"
  type        = string
}

variable "redshift_role_arn" {
  description = "Redshift IAM role ARN"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

