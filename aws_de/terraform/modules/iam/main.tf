terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Glue Service Role
resource "aws_iam_role" "glue_service" {
  name = "${var.environment}-retail-datalake-glue-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "glue_service_aws_managed" {
  role       = aws_iam_role.glue_service.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_service_custom" {
  name = "${var.environment}-retail-datalake-glue-service-policy"
  role = aws_iam_role.glue_service.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_datalake_bucket_arn,
          "${var.s3_datalake_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kafka:DescribeCluster",
          "kafka:GetBootstrapBrokers",
          "kafka:DescribeTopic",
          "kafka:DescribeConsumerGroup"
        ]
        Resource = var.msk_cluster_arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:${var.account_id}:log-group:/aws-glue/*"
      },
      {
        Effect = "Allow"
        Action = [
          "redshift:DescribeClusters",
          "redshift:DescribeClusterDbRevisions"
        ]
        Resource = "*"
      }
    ]
  })
}

# Redshift Role
resource "aws_iam_role" "redshift" {
  name = "${var.environment}-retail-datalake-redshift-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "redshift.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "redshift_s3" {
  name = "${var.environment}-retail-datalake-redshift-s3-policy"
  role = aws_iam_role.redshift.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_datalake_bucket_arn,
          "${var.s3_datalake_bucket_arn}/*"
        ]
      }
    ]
  })
}

# MSK Access Role (for Kafka clients)
resource "aws_iam_role" "msk_client" {
  name = "${var.environment}-retail-datalake-msk-client-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "msk_client" {
  name = "${var.environment}-retail-datalake-msk-client-policy"
  role = aws_iam_role.msk_client.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "kafka-cluster:Connect",
          "kafka-cluster:AlterCluster",
          "kafka-cluster:DescribeCluster"
        ]
        Resource = var.msk_cluster_arn
      },
      {
        Effect = "Allow"
        Action = [
          "kafka-cluster:*Topic*",
          "kafka-cluster:WriteData",
          "kafka-cluster:ReadData"
        ]
        Resource = "${var.msk_cluster_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "kafka-cluster:AlterGroup",
          "kafka-cluster:DescribeGroup"
        ]
        Resource = "${var.msk_cluster_arn}/*"
      }
    ]
  })
}

