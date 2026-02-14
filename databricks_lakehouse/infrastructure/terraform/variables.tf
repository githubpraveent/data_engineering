variable "databricks_workspace_url" {
  description = "Databricks workspace URL"
  type        = string
}

variable "databricks_token" {
  description = "Databricks API token"
  type        = string
  sensitive   = true
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "streaming_node_type" {
  description = "Node type for streaming cluster"
  type        = string
  default     = "i3.xlarge"
}

variable "streaming_num_workers" {
  description = "Number of workers for streaming cluster"
  type        = number
  default     = 2
}

variable "ml_node_type" {
  description = "Node type for ML cluster"
  type        = string
  default     = "g4dn.xlarge"
}

variable "ml_num_workers" {
  description = "Number of workers for ML cluster"
  type        = number
  default     = 1
}

variable "s3_bucket_name" {
  description = "S3 bucket name for Delta Lake storage"
  type        = string
}

variable "checkpoint_root" {
  description = "Root path for streaming checkpoints"
  type        = string
  default     = "s3://databricks-lakehouse/checkpoints/"
}
