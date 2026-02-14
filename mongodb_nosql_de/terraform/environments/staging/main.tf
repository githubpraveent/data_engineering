# Staging environment entry point
# Reference parent terraform configuration

module "infrastructure" {
  source = "../../"

  environment             = var.environment
  aws_region             = var.aws_region
  project_name           = var.project_name
  vpc_cidr               = var.vpc_cidr
  instance_type          = var.instance_type
  key_pair_name          = var.key_pair_name
  mongodb_atlas_api_key  = var.mongodb_atlas_api_key
  mongodb_atlas_api_secret = var.mongodb_atlas_api_secret
  mongodb_atlas_org_id   = var.mongodb_atlas_org_id
  mongodb_cluster_tier   = var.mongodb_cluster_tier
  mongodb_cluster_region = var.mongodb_cluster_region
}
