"""
Schema definitions for Bronze, Silver, and Gold layers of the retail data lakehouse.
This module contains Delta table schemas for all layers.
"""

from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    DecimalType, TimestampType, DateType, BooleanType, DoubleType
)

# ============================================================================
# BRONZE LAYER SCHEMAS (Raw/Ingested Data)
# ============================================================================

# Orders (raw from source system)
BRONZE_ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=True),
    StructField("order_date", StringType(), nullable=True),  # Raw string format
    StructField("order_status", StringType(), nullable=True),
    StructField("total_amount", StringType(), nullable=True),  # Raw string
    StructField("currency", StringType(), nullable=True),
    StructField("store_id", StringType(), nullable=True),
    StructField("payment_method", StringType(), nullable=True),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("raw_data", StringType(), nullable=True)  # Full JSON payload
])

# Customers (raw from source system)
BRONZE_CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", StringType(), nullable=False),
    StructField("first_name", StringType(), nullable=True),
    StructField("last_name", StringType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zip_code", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("date_of_birth", StringType(), nullable=True),
    StructField("registration_date", StringType(), nullable=True),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("raw_data", StringType(), nullable=True)
])

# Inventory (raw from source system)
BRONZE_INVENTORY_SCHEMA = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=True),
    StructField("quantity_on_hand", StringType(), nullable=True),  # Raw string
    StructField("quantity_reserved", StringType(), nullable=True),
    StructField("reorder_level", StringType(), nullable=True),
    StructField("last_updated", StringType(), nullable=True),
    StructField("unit_cost", StringType(), nullable=True),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("raw_data", StringType(), nullable=True)
])

# Sales Transactions (streaming events)
BRONZE_SALES_TRANSACTIONS_SCHEMA = StructType([
    StructField("transaction_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=True),
    StructField("product_id", StringType(), nullable=True),
    StructField("customer_id", StringType(), nullable=True),
    StructField("transaction_timestamp", TimestampType(), nullable=True),
    StructField("quantity", StringType(), nullable=True),
    StructField("unit_price", StringType(), nullable=True),
    StructField("discount_amount", StringType(), nullable=True),
    StructField("total_amount", StringType(), nullable=True),
    StructField("payment_method", StringType(), nullable=True),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("raw_data", StringType(), nullable=True)
])

# Products (raw from source system)
BRONZE_PRODUCTS_SCHEMA = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("product_name", StringType(), nullable=True),
    StructField("category", StringType(), nullable=True),
    StructField("subcategory", StringType(), nullable=True),
    StructField("brand", StringType(), nullable=True),
    StructField("description", StringType(), nullable=True),
    StructField("unit_price", StringType(), nullable=True),
    StructField("cost", StringType(), nullable=True),
    StructField("sku", StringType(), nullable=True),
    StructField("ingestion_timestamp", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("raw_data", StringType(), nullable=True)
])

# ============================================================================
# SILVER LAYER SCHEMAS (Cleaned/Refined Data)
# ============================================================================

# Orders (cleaned and validated)
SILVER_ORDERS_SCHEMA = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=True),
    StructField("order_date", DateType(), nullable=False),
    StructField("order_timestamp", TimestampType(), nullable=False),
    StructField("order_status", StringType(), nullable=False),
    StructField("total_amount", DecimalType(18, 2), nullable=False),
    StructField("currency", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=False),
    StructField("payment_method", StringType(), nullable=True),
    StructField("source_system", StringType(), nullable=False),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False),
    StructField("is_current", BooleanType(), nullable=False),
    StructField("version", IntegerType(), nullable=False)
])

# Customers (cleaned and deduplicated)
SILVER_CUSTOMERS_SCHEMA = StructType([
    StructField("customer_id", StringType(), nullable=False),
    StructField("first_name", StringType(), nullable=True),
    StructField("last_name", StringType(), nullable=True),
    StructField("full_name", StringType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zip_code", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("date_of_birth", DateType(), nullable=True),
    StructField("registration_date", DateType(), nullable=True),
    StructField("source_system", StringType(), nullable=False),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False),
    StructField("is_current", BooleanType(), nullable=False),
    StructField("version", IntegerType(), nullable=False)
])

# Inventory (cleaned and validated)
SILVER_INVENTORY_SCHEMA = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=False),
    StructField("quantity_on_hand", IntegerType(), nullable=False),
    StructField("quantity_reserved", IntegerType(), nullable=False),
    StructField("quantity_available", IntegerType(), nullable=False),
    StructField("reorder_level", IntegerType(), nullable=True),
    StructField("unit_cost", DecimalType(18, 2), nullable=True),
    StructField("last_updated", TimestampType(), nullable=False),
    StructField("source_system", StringType(), nullable=False),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False),
    StructField("is_current", BooleanType(), nullable=False),
    StructField("version", IntegerType(), nullable=False)
])

# Sales Transactions (cleaned streaming events)
SILVER_SALES_TRANSACTIONS_SCHEMA = StructType([
    StructField("transaction_id", StringType(), nullable=False),
    StructField("store_id", StringType(), nullable=False),
    StructField("product_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=True),
    StructField("transaction_timestamp", TimestampType(), nullable=False),
    StructField("quantity", IntegerType(), nullable=False),
    StructField("unit_price", DecimalType(18, 2), nullable=False),
    StructField("discount_amount", DecimalType(18, 2), nullable=False),
    StructField("total_amount", DecimalType(18, 2), nullable=False),
    StructField("payment_method", StringType(), nullable=True),
    StructField("source_system", StringType(), nullable=False),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False),
    StructField("is_current", BooleanType(), nullable=False)
])

# Products (cleaned)
SILVER_PRODUCTS_SCHEMA = StructType([
    StructField("product_id", StringType(), nullable=False),
    StructField("product_name", StringType(), nullable=False),
    StructField("category", StringType(), nullable=False),
    StructField("subcategory", StringType(), nullable=True),
    StructField("brand", StringType(), nullable=True),
    StructField("description", StringType(), nullable=True),
    StructField("unit_price", DecimalType(18, 2), nullable=False),
    StructField("cost", DecimalType(18, 2), nullable=True),
    StructField("sku", StringType(), nullable=True),
    StructField("source_system", StringType(), nullable=False),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False),
    StructField("is_current", BooleanType(), nullable=False),
    StructField("version", IntegerType(), nullable=False)
])

# ============================================================================
# GOLD LAYER SCHEMAS (Business-Level Tables)
# ============================================================================

# Fact: Sales Transactions
GOLD_FACT_SALES_SCHEMA = StructType([
    StructField("sales_id", StringType(), nullable=False),  # Surrogate key
    StructField("transaction_id", StringType(), nullable=False),
    StructField("date_key", IntegerType(), nullable=False),  # Foreign key to dim_date
    StructField("customer_key", IntegerType(), nullable=True),  # Foreign key to dim_customer
    StructField("product_key", IntegerType(), nullable=False),  # Foreign key to dim_product
    StructField("store_key", IntegerType(), nullable=False),  # Foreign key to dim_store
    StructField("transaction_timestamp", TimestampType(), nullable=False),
    StructField("quantity", IntegerType(), nullable=False),
    StructField("unit_price", DecimalType(18, 2), nullable=False),
    StructField("discount_amount", DecimalType(18, 2), nullable=False),
    StructField("total_amount", DecimalType(18, 2), nullable=False),
    StructField("cost_amount", DecimalType(18, 2), nullable=True),
    StructField("profit_amount", DecimalType(18, 2), nullable=True),
    StructField("payment_method", StringType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False)
])

# Dimension: Customer (SCD Type 2)
GOLD_DIM_CUSTOMER_SCHEMA = StructType([
    StructField("customer_key", IntegerType(), nullable=False),  # Surrogate key
    StructField("customer_id", StringType(), nullable=False),  # Natural key
    StructField("first_name", StringType(), nullable=True),
    StructField("last_name", StringType(), nullable=True),
    StructField("full_name", StringType(), nullable=True),
    StructField("email", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zip_code", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("date_of_birth", DateType(), nullable=True),
    StructField("registration_date", DateType(), nullable=True),
    StructField("effective_date", DateType(), nullable=False),  # SCD Type 2
    StructField("expiry_date", DateType(), nullable=True),  # SCD Type 2
    StructField("is_current", BooleanType(), nullable=False),  # SCD Type 2
    StructField("version", IntegerType(), nullable=False),  # SCD Type 2
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False)
])

# Dimension: Product (SCD Type 2)
GOLD_DIM_PRODUCT_SCHEMA = StructType([
    StructField("product_key", IntegerType(), nullable=False),  # Surrogate key
    StructField("product_id", StringType(), nullable=False),  # Natural key
    StructField("product_name", StringType(), nullable=False),
    StructField("category", StringType(), nullable=False),
    StructField("subcategory", StringType(), nullable=True),
    StructField("brand", StringType(), nullable=True),
    StructField("description", StringType(), nullable=True),
    StructField("unit_price", DecimalType(18, 2), nullable=False),
    StructField("cost", DecimalType(18, 2), nullable=True),
    StructField("sku", StringType(), nullable=True),
    StructField("effective_date", DateType(), nullable=False),  # SCD Type 2
    StructField("expiry_date", DateType(), nullable=True),  # SCD Type 2
    StructField("is_current", BooleanType(), nullable=False),  # SCD Type 2
    StructField("version", IntegerType(), nullable=False),  # SCD Type 2
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False)
])

# Dimension: Store (SCD Type 1 - overwrite)
GOLD_DIM_STORE_SCHEMA = StructType([
    StructField("store_key", IntegerType(), nullable=False),  # Surrogate key
    StructField("store_id", StringType(), nullable=False),  # Natural key
    StructField("store_name", StringType(), nullable=False),
    StructField("store_type", StringType(), nullable=True),
    StructField("address", StringType(), nullable=True),
    StructField("city", StringType(), nullable=True),
    StructField("state", StringType(), nullable=True),
    StructField("zip_code", StringType(), nullable=True),
    StructField("country", StringType(), nullable=True),
    StructField("phone", StringType(), nullable=True),
    StructField("manager_name", StringType(), nullable=True),
    StructField("opening_date", DateType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False)
])

# Dimension: Date
GOLD_DIM_DATE_SCHEMA = StructType([
    StructField("date_key", IntegerType(), nullable=False),  # YYYYMMDD format
    StructField("date", DateType(), nullable=False),
    StructField("day", IntegerType(), nullable=False),
    StructField("month", IntegerType(), nullable=False),
    StructField("year", IntegerType(), nullable=False),
    StructField("quarter", IntegerType(), nullable=False),
    StructField("week_of_year", IntegerType(), nullable=False),
    StructField("day_of_week", IntegerType(), nullable=False),
    StructField("day_name", StringType(), nullable=False),
    StructField("month_name", StringType(), nullable=False),
    StructField("is_weekend", BooleanType(), nullable=False),
    StructField("is_holiday", BooleanType(), nullable=False),
    StructField("holiday_name", StringType(), nullable=True)
])

# Aggregated: Daily Sales Summary
GOLD_AGG_DAILY_SALES_SCHEMA = StructType([
    StructField("date_key", IntegerType(), nullable=False),
    StructField("store_key", IntegerType(), nullable=False),
    StructField("product_key", IntegerType(), nullable=False),
    StructField("total_quantity", IntegerType(), nullable=False),
    StructField("total_sales_amount", DecimalType(18, 2), nullable=False),
    StructField("total_cost_amount", DecimalType(18, 2), nullable=False),
    StructField("total_profit_amount", DecimalType(18, 2), nullable=False),
    StructField("transaction_count", IntegerType(), nullable=False),
    StructField("updated_at", TimestampType(), nullable=False)
])


def get_schema(schema_name: str) -> StructType:
    """
    Helper function to retrieve a schema by name.
    
    Args:
        schema_name: Name of the schema (e.g., 'BRONZE_ORDERS_SCHEMA')
        
    Returns:
        StructType schema
    """
    schema_map = {
        'BRONZE_ORDERS_SCHEMA': BRONZE_ORDERS_SCHEMA,
        'BRONZE_CUSTOMERS_SCHEMA': BRONZE_CUSTOMERS_SCHEMA,
        'BRONZE_INVENTORY_SCHEMA': BRONZE_INVENTORY_SCHEMA,
        'BRONZE_SALES_TRANSACTIONS_SCHEMA': BRONZE_SALES_TRANSACTIONS_SCHEMA,
        'BRONZE_PRODUCTS_SCHEMA': BRONZE_PRODUCTS_SCHEMA,
        'SILVER_ORDERS_SCHEMA': SILVER_ORDERS_SCHEMA,
        'SILVER_CUSTOMERS_SCHEMA': SILVER_CUSTOMERS_SCHEMA,
        'SILVER_INVENTORY_SCHEMA': SILVER_INVENTORY_SCHEMA,
        'SILVER_SALES_TRANSACTIONS_SCHEMA': SILVER_SALES_TRANSACTIONS_SCHEMA,
        'SILVER_PRODUCTS_SCHEMA': SILVER_PRODUCTS_SCHEMA,
        'GOLD_FACT_SALES_SCHEMA': GOLD_FACT_SALES_SCHEMA,
        'GOLD_DIM_CUSTOMER_SCHEMA': GOLD_DIM_CUSTOMER_SCHEMA,
        'GOLD_DIM_PRODUCT_SCHEMA': GOLD_DIM_PRODUCT_SCHEMA,
        'GOLD_DIM_STORE_SCHEMA': GOLD_DIM_STORE_SCHEMA,
        'GOLD_DIM_DATE_SCHEMA': GOLD_DIM_DATE_SCHEMA,
        'GOLD_AGG_DAILY_SALES_SCHEMA': GOLD_AGG_DAILY_SALES_SCHEMA
    }
    
    if schema_name not in schema_map:
        raise ValueError(f"Schema '{schema_name}' not found. Available schemas: {list(schema_map.keys())}")
    
    return schema_map[schema_name]

