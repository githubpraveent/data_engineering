terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# S3 Data Lake Bucket
resource "aws_s3_bucket" "datalake" {
  bucket = "retail-datalake-${var.environment}-${var.account_id}"

  tags = merge(
    var.tags,
    {
      Name = "retail-datalake-${var.environment}"
    }
  )
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  versioning_configuration {
    status = var.environment == "prod" ? "Enabled" : "Disabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  rule {
    id     = "landing-zone-transition"
    status = "Enabled"

    filter {
      prefix = "landing/"
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "staging-zone-transition"
    status = "Enabled"

    filter {
      prefix = "staging/"
    }

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 730
    }
  }

  rule {
    id     = "curated-zone-retention"
    status = "Enabled"

    filter {
      prefix = "curated/"
    }

    # Curated zone data retained indefinitely
  }
}

# S3 Bucket Policy for Glue and Redshift access
resource "aws_s3_bucket_policy" "datalake" {
  bucket = aws_s3_bucket.datalake.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "GlueAccess"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.datalake.arn,
          "${aws_s3_bucket.datalake.arn}/*"
        ]
      },
      {
        Sid    = "RedshiftAccess"
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.datalake.arn,
          "${aws_s3_bucket.datalake.arn}/*"
        ]
      }
    ]
  })
}

