# Terraform outputs

output "databricks_workspace_url" {
  description = "Databricks workspace URL"
  value       = try(databricks_mws_workspaces.retail_workspace.workspace_url, "N/A")
}

output "unity_catalog_metastore_id" {
  description = "Unity Catalog metastore ID"
  value       = try(databricks_mws_metastores.metastore.metastore_id, "N/A")
}

output "unity_catalog_catalog_name" {
  description = "Unity Catalog catalog name"
  value       = try(databricks_catalog.retail_catalog.name, "N/A")
}

output "sql_warehouse_id" {
  description = "SQL Warehouse ID"
  value       = try(databricks_sql_endpoint.analytics_warehouse.id, "N/A")
}

output "s3_bucket_name" {
  description = "S3 bucket for Unity Catalog"
  value       = try(aws_s3_bucket.unity_catalog.bucket, "N/A")
}

output "cluster_id" {
  description = "Job cluster ID"
  value       = try(databricks_cluster.job_cluster.cluster_id, "N/A")
}

