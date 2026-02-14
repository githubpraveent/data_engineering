output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "s3_datalake_bucket" {
  description = "S3 Data Lake bucket name"
  value       = module.s3_datalake.bucket_name
}

output "msk_cluster_arn" {
  description = "MSK cluster ARN"
  value       = module.msk.cluster_arn
}

output "msk_bootstrap_brokers" {
  description = "MSK bootstrap broker addresses"
  value       = module.msk.bootstrap_brokers
  sensitive   = true
}

output "redshift_cluster_endpoint" {
  description = "Redshift cluster endpoint"
  value       = module.redshift.cluster_endpoint
  sensitive   = true
}

output "glue_database_name" {
  description = "Glue Data Catalog database name"
  value       = module.glue.database_name
}

output "glue_job_names" {
  description = "Glue job names"
  value       = module.glue.job_names
}

