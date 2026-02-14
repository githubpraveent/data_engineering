output "glue_service_role_arn" {
  description = "Glue service role ARN"
  value       = aws_iam_role.glue_service.arn
}

output "redshift_role_arn" {
  description = "Redshift role ARN"
  value       = aws_iam_role.redshift.arn
}

output "msk_client_role_arn" {
  description = "MSK client role ARN"
  value       = aws_iam_role.msk_client.arn
}

