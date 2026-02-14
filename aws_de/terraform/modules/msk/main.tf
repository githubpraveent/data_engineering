terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# MSK Cluster
resource "aws_msk_cluster" "main" {
  cluster_name           = "${var.environment}-retail-datalake-msk"
  kafka_version          = var.kafka_version
  number_of_broker_nodes = var.broker_count

  broker_node_group_info {
    instance_type   = var.instance_type
    client_subnets  = var.subnet_ids
    security_groups = var.security_group_ids
    storage_info {
      ebs_storage_info {
        volume_size = var.storage_size
      }
    }
  }

  encryption_info {
    encryption_at_rest_kms_key_id = aws_kms_key.msk.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  client_authentication {
    sasl {
      iam = true
    }
    tls {
      certificate_authority_arns = []
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.main.arn
    revision = aws_msk_configuration.main.latest_revision
  }

  logging_info {
    broker_logs {
      cloudwatch_logs {
        enabled   = true
        log_group = aws_cloudwatch_log_group.msk.name
      }
    }
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-retail-datalake-msk"
    }
  )
}

# MSK Configuration
resource "aws_msk_configuration" "main" {
  kafka_versions = [var.kafka_version]
  name           = "${var.environment}-retail-datalake-msk-config"

  server_properties = <<PROPERTIES
auto.create.topics.enable=true
default.replication.factor=3
min.insync.replicas=2
num.partitions=3
log.retention.hours=168
compression.type=snappy
PROPERTIES
}

# KMS Key for MSK Encryption
resource "aws_kms_key" "msk" {
  description             = "KMS key for MSK cluster encryption"
  deletion_window_in_days = 7

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-retail-datalake-msk-kms"
    }
  )
}

resource "aws_kms_alias" "msk" {
  name          = "alias/${var.environment}-retail-datalake-msk"
  target_key_id = aws_kms_key.msk.key_id
}

# CloudWatch Log Group for MSK
resource "aws_cloudwatch_log_group" "msk" {
  name              = "/aws/msk/${var.environment}-retail-datalake"
  retention_in_days = 7

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-retail-datalake-msk-logs"
    }
  )
}

# MSK Topics (created via Kafka admin API, not Terraform)
# Topics are managed via Ansible or Kafka admin tools
# Example topics:
# - retail.customer.cdc
# - retail.order.cdc
# - retail.product.cdc
# - retail.order_item.cdc

