/**
 * Monitoring Module
 * 
 * Sets up CloudWatch dashboards, alarms, and logging for the data pipeline.
 * Monitors pipeline execution, errors, and data quality metrics.
 */

# CloudWatch Log Group (define before dashboard to reference it)
resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/aws/${var.project_name}/${var.environment}/pipeline"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "pipeline" {
  dashboard_name = "${var.project_name}-${var.environment}-pipeline-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", { stat = "Average" }],
            ["AWS/EC2", "NetworkIn", { stat = "Sum" }],
            ["AWS/EC2", "NetworkOut", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "EC2 Instance Metrics"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6

        properties = {
          query = "SOURCE '${aws_cloudwatch_log_group.pipeline.name}' | fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100"
          region = "us-east-1"
          title  = "Pipeline Error Logs"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["${var.project_name}/${var.environment}/pipeline", "records_processed", { stat = "Sum" }],
            ["${var.project_name}/${var.environment}/pipeline", "records_failed", { stat = "Sum" }],
            ["${var.project_name}/${var.environment}/pipeline", "data_quality_score", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"
          title  = "Pipeline Execution Metrics"
        }
      }
    ]
  })
}

# Alarm for High CPU Usage
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-${var.environment}-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This metric monitors EC2 CPU utilization"
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = "*"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Alarm for Pipeline Failures
resource "aws_cloudwatch_metric_alarm" "pipeline_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-pipeline-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "records_failed"
  namespace           = "${var.project_name}/${var.environment}/pipeline"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when pipeline fails to process records"
  treat_missing_data  = "notBreaching"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Alarm for Low Data Quality Score
resource "aws_cloudwatch_metric_alarm" "low_data_quality" {
  alarm_name          = "${var.project_name}-${var.environment}-low-data-quality"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "data_quality_score"
  namespace           = "${var.project_name}/${var.environment}/pipeline"
  period              = 300
  statistic           = "Average"
  threshold           = 0.9
  alarm_description   = "Alert when data quality score drops below 90%"
  treat_missing_data  = "breaching"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic for Alarms
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.environment}-alerts"

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# SNS Topic Subscription (optional - configure email/endpoint)
# resource "aws_sns_topic_subscription" "email" {
#   topic_arn = aws_sns_topic.alerts.arn
#   protocol  = "email"
#   endpoint  = "admin@example.com"
# }
