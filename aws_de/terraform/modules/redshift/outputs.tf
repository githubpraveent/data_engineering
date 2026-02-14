output "cluster_id" {
  description = "Redshift cluster identifier"
  value       = aws_redshift_cluster.main.cluster_identifier
}

output "cluster_endpoint" {
  description = "Redshift cluster endpoint"
  value       = "${aws_redshift_cluster.main.endpoint}:${aws_redshift_cluster.main.port}"
  sensitive   = true
}

output "cluster_arn" {
  description = "Redshift cluster ARN"
  value       = aws_redshift_cluster.main.arn
}

