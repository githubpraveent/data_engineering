output "namespace_name" {
  description = "Event Hubs namespace name"
  value       = azurerm_eventhub_namespace.main.name
}

output "namespace_id" {
  description = "Event Hubs namespace ID"
  value       = azurerm_eventhub_namespace.main.id
}

output "pos_event_hub_name" {
  description = "POS events Event Hub name"
  value       = azurerm_eventhub.pos_events.name
}

output "order_event_hub_name" {
  description = "Order events Event Hub name"
  value       = azurerm_eventhub.order_events.name
}

output "connection_string" {
  description = "Event Hubs connection string (sensitive)"
  value       = azurerm_eventhub_authorization_rule.databricks.primary_connection_string
  sensitive   = true
}

