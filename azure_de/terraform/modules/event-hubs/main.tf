# Event Hubs Namespace
resource "azurerm_eventhub_namespace" "main" {
  name                = "${var.environment}-${var.project_name}-ehns"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = var.sku
  capacity            = var.capacity

  # Enable auto-inflate for scaling
  auto_inflate_enabled     = true
  maximum_throughput_units = var.max_throughput_units

  tags = var.tags
}

# Event Hub for POS events
resource "azurerm_eventhub" "pos_events" {
  name                = "pos-events"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group_name
  partition_count     = 4
  message_retention   = 7 # days
}

# Event Hub for order events
resource "azurerm_eventhub" "order_events" {
  name                = "order-events"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group_name
  partition_count     = 4
  message_retention   = 7
}

# Consumer Groups
resource "azurerm_eventhub_consumer_group" "databricks_streaming" {
  name                = "databricks-streaming"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.pos_events.name
  resource_group_name = var.resource_group_name
}

resource "azurerm_eventhub_consumer_group" "databricks_order_streaming" {
  name                = "databricks-streaming"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.order_events.name
  resource_group_name = var.resource_group_name
}

# Authorization Rule for Databricks
resource "azurerm_eventhub_authorization_rule" "databricks" {
  name                = "databricks-access"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.pos_events.name
  resource_group_name = var.resource_group_name
  listen              = true
  send                = false
  manage              = false
}

