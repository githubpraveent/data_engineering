terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Redshift Subnet Group
resource "aws_redshift_subnet_group" "main" {
  name       = "${var.environment}-retail-datalake-redshift-subnet-group"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-retail-datalake-redshift-subnet-group"
    }
  )
}

# Redshift Parameter Group
resource "aws_redshift_parameter_group" "main" {
  name   = "${var.environment}-retail-datalake-redshift-params"
  family = "redshift-1.0"

  parameter {
    name  = "enable_user_activity_logging"
    value = "true"
  }

  parameter {
    name  = "query_group"
    value = "default"
  }

  tags = var.tags
}

# Redshift Cluster
resource "aws_redshift_cluster" "main" {
  cluster_identifier  = "${var.environment}-retail-datalake-redshift"
  database_name       = var.database_name
  master_username     = var.master_username
  master_password     = var.master_password
  node_type           = var.node_type
  number_of_nodes     = var.number_of_nodes
  cluster_type        = var.number_of_nodes > 1 ? "multi-node" : "single-node"

  vpc_security_group_ids = var.security_group_ids
  cluster_subnet_group_name = aws_redshift_subnet_group.main.name
  parameter_group_name      = aws_redshift_parameter_group.main.name

  publicly_accessible = false
  encrypted           = true
  enhanced_vpc_routing = true

  iam_roles = [var.redshift_role_arn]

  logging {
    enable        = true
    bucket_name   = var.s3_datalake_bucket
    s3_key_prefix = "redshift-logs/"
  }

  snapshot_copy {
    destination_region = data.aws_region.current.name
    retention_period   = 7
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-retail-datalake-redshift"
    }
  )

  depends_on = [aws_redshift_subnet_group.main]
}

# Redshift IAM Role Association
resource "aws_redshift_cluster_iam_roles" "main" {
  cluster_identifier = aws_redshift_cluster.main.cluster_identifier
  iam_role_arns      = [var.redshift_role_arn]
}

data "aws_region" "current" {}

