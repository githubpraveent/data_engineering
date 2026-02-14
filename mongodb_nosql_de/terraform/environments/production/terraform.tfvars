# Production Environment Configuration

environment  = "production"
aws_region   = "us-east-1"
project_name = "mongodb-pipeline"
vpc_cidr     = "10.1.0.0/16"

instance_type     = "t3.medium"
key_pair_name     = "production-key-pair"  # Update with your key pair name

mongodb_cluster_tier   = "M20"
mongodb_cluster_region = "US_EAST_1"

# These should be set via environment variables or terraform.tfvars (not committed)
# mongodb_atlas_api_key    = var.mongodb_atlas_api_key
# mongodb_atlas_api_secret = var.mongodb_atlas_api_secret
# mongodb_atlas_org_id     = var.mongodb_atlas_org_id
