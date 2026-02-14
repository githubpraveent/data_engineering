output "cluster_name" {
  description = "MongoDB cluster name"
  value       = mongodbatlas_cluster.main.name
}

output "connection_string" {
  description = "MongoDB connection string"
  value       = local.connection_string
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = "data_pipeline"
}

output "username" {
  description = "Database username"
  value       = mongodbatlas_database_user.pipeline_user.username
}

output "password" {
  description = "Database password"
  value       = mongodbatlas_database_user.pipeline_user.password
  sensitive   = true
}

output "project_id" {
  description = "MongoDB Atlas project ID"
  value       = mongodbatlas_project.main.id
}
