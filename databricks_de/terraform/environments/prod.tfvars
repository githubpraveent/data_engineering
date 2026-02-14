# Production environment configuration

environment             = "prod"
aws_region              = "us-east-1"
aws_zone_id             = "us-east-1a"
node_type_id            = "i3.2xlarge"  # Larger instance for production
num_workers             = 4              # More workers for production

tags = {
  Environment = "prod"
  Project     = "retail-datalake"
  Team        = "data-engineering"
  CostCenter  = "engineering"
}

