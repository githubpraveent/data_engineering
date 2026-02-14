# Pub/Sub Module
# Creates topics and subscriptions for streaming data ingestion

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, qa, prod)"
  type        = string
}

variable "topics" {
  description = "Map of topic names to their configurations"
  type = map(object({
    message_retention_duration = string
    labels                     = map(string)
  }))
  default = {
    retail-transactions = {
      message_retention_duration = "604800s"  # 7 days
      labels = {
        source = "transactional-db"
        type   = "cdc"
      }
    }
    retail-inventory = {
      message_retention_duration = "604800s"
      labels = {
        source = "inventory-system"
        type   = "updates"
      }
    }
    retail-customers = {
      message_retention_duration = "604800s"
      labels = {
        source = "crm-system"
        type   = "events"
      }
    }
  }
}

variable "subscriptions" {
  description = "Map of subscription names to their topic and configuration"
  type = map(object({
    topic                 = string
    ack_deadline_seconds  = number
    message_retention_duration = string
    expiration_policy_ttl = string
  }))
  default = {
    retail-transactions-dataflow = {
      topic                 = "retail-transactions"
      ack_deadline_seconds  = 60
      message_retention_duration = "604800s"
      expiration_policy_ttl = "2592000s"  # 30 days
    }
    retail-inventory-dataflow = {
      topic                 = "retail-inventory"
      ack_deadline_seconds  = 60
      message_retention_duration = "604800s"
      expiration_policy_ttl = "2592000s"
    }
    retail-customers-dataflow = {
      topic                 = "retail-customers"
      ack_deadline_seconds  = 60
      message_retention_duration = "604800s"
      expiration_policy_ttl = "2592000s"
    }
  }
}

# Create Topics
resource "google_pubsub_topic" "topics" {
  for_each = var.topics

  name    = "${each.key}-${var.environment}"
  project = var.project_id

  message_retention_duration = each.value.message_retention_duration

  labels = merge(
    each.value.labels,
    {
      environment = var.environment
    }
  )
}

# Create Subscriptions
resource "google_pubsub_subscription" "subscriptions" {
  for_each = var.subscriptions

  name    = "${each.key}-${var.environment}"
  topic   = google_pubsub_topic.topics[each.value.topic].name
  project = var.project_id

  ack_deadline_seconds = each.value.ack_deadline_seconds

  message_retention_duration = each.value.message_retention_duration

  expiration_policy {
    ttl = each.value.expiration_policy_ttl
  }

  labels = {
    environment = var.environment
    purpose     = "dataflow-consumer"
  }
}

# Outputs
output "topic_names" {
  value       = { for k, v in google_pubsub_topic.topics : k => v.name }
  description = "Map of topic keys to topic names"
}

output "subscription_names" {
  value       = { for k, v in google_pubsub_subscription.subscriptions : k => v.name }
  description = "Map of subscription keys to subscription names"
}

output "topic_ids" {
  value       = { for k, v in google_pubsub_topic.topics : k => v.id }
  description = "Map of topic keys to topic IDs"
}

