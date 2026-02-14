variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "qa", "prod"], var.environment)
    error_message = "Environment must be dev, qa, or prod."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# MSK Variables
variable "msk_kafka_version" {
  description = "Kafka version for MSK cluster"
  type        = string
  default     = "3.5.1"
}

variable "msk_instance_type" {
  description = "Instance type for MSK brokers"
  type        = string
  default     = "kafka.m5.large"
}

variable "msk_broker_count" {
  description = "Number of MSK brokers"
  type        = number
  default     = 3
}

variable "msk_storage_size" {
  description = "Storage size per broker in GB"
  type        = number
  default     = 100
}

# Redshift Variables
variable "redshift_node_type" {
  description = "Redshift node type"
  type        = string
  default     = "dc2.large"
}

variable "redshift_number_of_nodes" {
  description = "Number of Redshift nodes"
  type        = number
  default     = 2
}

variable "redshift_database_name" {
  description = "Redshift database name"
  type        = string
  default     = "retail_dw"
}

variable "redshift_master_username" {
  description = "Redshift master username"
  type        = string
  default     = "admin"
  sensitive   = true
}

variable "redshift_master_password" {
  description = "Redshift master password"
  type        = string
  sensitive   = true
}

# Local values
locals {
  common_tags = {
    Project     = "retail-datalake"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

