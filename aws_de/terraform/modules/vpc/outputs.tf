output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "msk_security_group_id" {
  description = "MSK security group ID"
  value       = aws_security_group.msk.id
}

output "glue_security_group_id" {
  description = "Glue security group ID"
  value       = aws_security_group.glue.id
}

output "redshift_security_group_id" {
  description = "Redshift security group ID"
  value       = aws_security_group.redshift.id
}

