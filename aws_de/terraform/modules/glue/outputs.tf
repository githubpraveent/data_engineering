output "database_name" {
  description = "Glue Data Catalog database name"
  value       = aws_glue_catalog_database.datalake.name
}

output "job_names" {
  description = "List of Glue job names"
  value = [
    aws_glue_job.streaming_customer.name,
    aws_glue_job.streaming_order.name,
    aws_glue_job.batch_landing_to_staging.name,
    aws_glue_job.batch_staging_to_curated.name
  ]
}

