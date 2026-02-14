terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# CloudWatch Alarm - MSK Consumer Lag
resource "aws_cloudwatch_metric_alarm" "msk_consumer_lag" {
  alarm_name          = "${var.environment}-retail-datalake-msk-consumer-lag"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "SumOffsetLag"
  namespace           = "AWS/Kafka"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"
  alarm_description   = "This metric monitors MSK consumer lag"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterName = var.msk_cluster_name
  }

  tags = var.tags
}

# CloudWatch Alarm - Glue Job Failure
resource "aws_cloudwatch_metric_alarm" "glue_job_failure" {
  for_each = toset(var.glue_job_names)

  alarm_name          = "${var.environment}-retail-datalake-glue-${each.key}-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "glue.driver.ExecutorAllocationManager.executors.numberAllExecutors"
  namespace           = "Glue"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Glue job failures"
  treat_missing_data  = "notBreaching"

  dimensions = {
    JobName = each.key
  }

  tags = var.tags
}

# CloudWatch Alarm - Redshift CPU Utilization
resource "aws_cloudwatch_metric_alarm" "redshift_cpu" {
  alarm_name          = "${var.environment}-retail-datalake-redshift-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/Redshift"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors Redshift CPU utilization"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ClusterIdentifier = var.redshift_cluster_id
  }

  tags = var.tags
}

