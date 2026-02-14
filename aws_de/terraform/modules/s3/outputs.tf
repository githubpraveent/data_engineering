output "bucket_name" {
  description = "S3 Data Lake bucket name"
  value       = aws_s3_bucket.datalake.id
}

output "bucket_arn" {
  description = "S3 Data Lake bucket ARN"
  value       = aws_s3_bucket.datalake.arn
}

