# Development environment configuration

environment             = "dev"
aws_region              = "us-east-1"
aws_zone_id             = "us-east-1a"
node_type_id            = "i3.xlarge"
num_workers             = 2

# Databricks configuration (set via environment variables or Terraform Cloud)
# databricks_host        = "https://dev-workspace.cloud.databricks.com"
# databricks_token       = "YOUR_TOKEN_HERE"
# databricks_account_id  = "YOUR_ACCOUNT_ID"

tags = {
  Environment = "dev"
  Project     = "retail-datalake"
  Team        = "data-engineering"
}

