variable "environment" {
  description = "Environment name"
  type        = string
}

variable "account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

