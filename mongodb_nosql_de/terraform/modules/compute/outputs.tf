output "instance_ids" {
  description = "EC2 instance IDs"
  value       = aws_instance.pipeline[*].id
}

output "instance_public_ips" {
  description = "EC2 instance public IPs"
  value       = aws_instance.pipeline[*].public_ip
}

output "instance_private_ips" {
  description = "EC2 instance private IPs"
  value       = aws_instance.pipeline[*].private_ip
}

output "pipeline_function_name" {
  description = "Pipeline function/service name for monitoring"
  value       = "${var.project_name}-${var.environment}-pipeline"
}

output "iam_role_arn" {
  description = "IAM role ARN for pipeline servers"
  value       = aws_iam_role.pipeline.arn
}
