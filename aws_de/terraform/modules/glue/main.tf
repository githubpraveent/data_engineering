terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Glue Data Catalog Database
resource "aws_glue_catalog_database" "datalake" {
  name        = "${var.environment}_retail_datalake"
  description = "Data Catalog database for retail data lake"

  tags = var.tags
}

# Glue Crawler for Landing Zone
resource "aws_glue_crawler" "landing" {
  database_name = aws_glue_catalog_database.datalake.name
  name          = "${var.environment}-retail-datalake-landing-crawler"
  role          = var.glue_service_role_arn

  s3_target {
    path = "s3://${var.s3_datalake_bucket}/landing/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = var.tags
}

# Glue Crawler for Staging Zone
resource "aws_glue_crawler" "staging" {
  database_name = aws_glue_catalog_database.datalake.name
  name          = "${var.environment}-retail-datalake-staging-crawler"
  role          = var.glue_service_role_arn

  s3_target {
    path = "s3://${var.s3_datalake_bucket}/staging/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = var.tags
}

# Glue Crawler for Curated Zone
resource "aws_glue_crawler" "curated" {
  database_name = aws_glue_catalog_database.datalake.name
  name          = "${var.environment}-retail-datalake-curated-crawler"
  role          = var.glue_service_role_arn

  s3_target {
    path = "s3://${var.s3_datalake_bucket}/curated/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = var.tags
}

# Glue Streaming Job - Customer CDC
resource "aws_glue_job" "streaming_customer" {
  name     = "${var.environment}-retail-streaming-customer"
  role_arn = var.glue_service_role_arn

  command {
    name            = "gluestreaming"
    script_location = "s3://${var.s3_datalake_bucket}/scripts/glue/streaming/customer_streaming.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"              = "python"
    "--job-bookmark-option"       = "job-bookmark-enable"
    "--enable-metrics"            = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--kafka.bootstrap.servers"   = var.msk_bootstrap_servers
    "--kafka.topic"               = "retail.customer.cdc"
    "--kafka.startingPosition"    = "TRIM_HORIZON"
    "--kafka.security.protocol"   = "SASL_SSL"
    "--kafka.sasl.mechanism"      = "AWS_MSK_IAM"
    "--kafka.sasl.jaas.config"    = "software.amazon.msk.auth.iam.IAMLoginModule required;"
    "--kafka.sasl.client.callback.handler.class" = "software.amazon.msk.auth.iam.IAMClientCallbackHandler"
    "--s3_target_path"            = "s3://${var.s3_datalake_bucket}/landing/customer/"
    "--TempDir"                   = "s3://${var.s3_datalake_bucket}/temp/"
  }

  worker_type       = "G.1X"
  number_of_workers = 2

  glue_version = "4.0"

  tags = var.tags
}

# Glue Streaming Job - Order CDC
resource "aws_glue_job" "streaming_order" {
  name     = "${var.environment}-retail-streaming-order"
  role_arn = var.glue_service_role_arn

  command {
    name            = "gluestreaming"
    script_location = "s3://${var.s3_datalake_bucket}/scripts/glue/streaming/order_streaming.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"              = "python"
    "--job-bookmark-option"       = "job-bookmark-enable"
    "--enable-metrics"            = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--kafka.bootstrap.servers"   = var.msk_bootstrap_servers
    "--kafka.topic"               = "retail.order.cdc"
    "--kafka.startingPosition"    = "TRIM_HORIZON"
    "--kafka.security.protocol"   = "SASL_SSL"
    "--kafka.sasl.mechanism"      = "AWS_MSK_IAM"
    "--kafka.sasl.jaas.config"    = "software.amazon.msk.auth.iam.IAMLoginModule required;"
    "--kafka.sasl.client.callback.handler.class" = "software.amazon.msk.auth.iam.IAMClientCallbackHandler"
    "--s3_target_path"            = "s3://${var.s3_datalake_bucket}/landing/order/"
    "--TempDir"                   = "s3://${var.s3_datalake_bucket}/temp/"
  }

  worker_type       = "G.1X"
  number_of_workers = 2

  glue_version = "4.0"

  tags = var.tags
}

# Glue Batch Job - Landing to Staging
resource "aws_glue_job" "batch_landing_to_staging" {
  name     = "${var.environment}-retail-batch-landing-to-staging"
  role_arn = var.glue_service_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.s3_datalake_bucket}/scripts/glue/batch/landing_to_staging.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"              = "python"
    "--enable-metrics"            = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                   = "s3://${var.s3_datalake_bucket}/temp/"
    "--s3_landing_path"           = "s3://${var.s3_datalake_bucket}/landing/"
    "--s3_staging_path"           = "s3://${var.s3_datalake_bucket}/staging/"
  }

  worker_type       = "G.1X"
  number_of_workers = 2

  glue_version = "4.0"

  tags = var.tags
}

# Glue Batch Job - Staging to Curated
resource "aws_glue_job" "batch_staging_to_curated" {
  name     = "${var.environment}-retail-batch-staging-to-curated"
  role_arn = var.glue_service_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.s3_datalake_bucket}/scripts/glue/batch/staging_to_curated.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"              = "python"
    "--enable-metrics"            = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--TempDir"                   = "s3://${var.s3_datalake_bucket}/temp/"
    "--s3_staging_path"           = "s3://${var.s3_datalake_bucket}/staging/"
    "--s3_curated_path"           = "s3://${var.s3_datalake_bucket}/curated/"
  }

  worker_type       = "G.2X"
  number_of_workers = 4

  glue_version = "4.0"

  tags = var.tags
}

# Glue Trigger - Schedule for Batch Jobs
resource "aws_glue_trigger" "batch_schedule" {
  name     = "${var.environment}-retail-batch-schedule"
  type     = "SCHEDULED"
  schedule = "cron(0 2 * * ? *)" # Daily at 2 AM UTC

  actions {
    job_name = aws_glue_job.batch_landing_to_staging.name
  }

  actions {
    job_name = aws_glue_job.batch_staging_to_curated.name
  }

  tags = var.tags
}

