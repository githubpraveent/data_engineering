# Redshift Data Warehouse

This directory contains Redshift SQL scripts for schema definitions, SCD processing, and fact table loading.

## Structure

```
redshift/
├── schemas/              # Schema DDL
│   ├── staging.sql      # Staging schema (raw data)
│   └── analytics.sql    # Analytics schema (star schema)
├── scd/                 # Slowly Changing Dimension procedures
│   ├── scd_type1_product.sql
│   └── scd_type2_customer.sql
├── facts/               # Fact table loading
│   └── load_sales_fact.sql
├── streaming/           # Streaming ingestion (MSK → Redshift)
│   ├── customer_streaming_mv.sql
│   └── order_streaming_mv.sql
└── aggregates/          # Aggregate tables
    └── refresh_sales_summary.sql
```

## Schemas

### Staging Schema
- Raw tables for data ingested from Kafka and S3
- Tables: `customer_streaming`, `order_streaming`, `customer_batch`, `order_batch`, etc.

### Analytics Schema
- Star schema for data warehouse
- Dimensions: `dim_date`, `dim_customer`, `dim_product`
- Facts: `fact_sales`, `fact_sales_summary`

## SCD Processing

### Type 1 (Overwrite)
- **Product Dimension**: Updates overwrite existing records
- No history maintained
- Use for attributes that don't need historical tracking

### Type 2 (History)
- **Customer Dimension**: Maintains full history
- Effective dates and current flag
- Use for attributes that need historical tracking

## Fact Loading

### Sales Fact
- Incremental load from staging tables
- Joins dimensions to get surrogate keys
- Handles new orders only (incremental)

## Streaming Ingestion

Materialized views consume directly from MSK topics:
- `mv_customer_streaming`: Customer CDC events
- `mv_order_streaming`: Order CDC events

Auto-refresh enabled for near real-time updates.

## Usage

### Deploy Schemas
```bash
psql -h <redshift-endpoint> -U admin -d retail_dw -f schemas/staging.sql
psql -h <redshift-endpoint> -U admin -d retail_dw -f schemas/analytics.sql
```

### Run SCD Procedures
```sql
CALL analytics.sp_scd_type1_product();
CALL analytics.sp_scd_type2_customer();
```

### Load Facts
```sql
CALL analytics.sp_load_sales_fact();
```

### Refresh Aggregates
```sql
CALL analytics.sp_refresh_sales_summary();
```

## Scheduling

Procedures can be scheduled via:
- Redshift Query Scheduler
- AWS EventBridge
- External scheduler (Airflow, etc.)

