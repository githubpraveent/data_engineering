# dbt Retail Data Warehouse Project

This dbt project transforms raw retail data into a dimensional data warehouse.

## Project Structure

```
models/
├── staging/          # Clean and standardize raw data
├── intermediate/     # Business logic and joins
├── dimensions/       # Dimension tables (SCD Type 1 & 2)
├── facts/            # Fact tables (transactional & snapshot)
└── marts/            # Aggregated business metrics

macros/               # Reusable SQL macros
tests/                # Custom data quality tests
snapshots/            # dbt snapshots for change tracking
```

## Models

### Staging Models
- `stg_orders`: Clean order transactions
- `stg_customers`: Clean customer data
- `stg_products`: Clean product catalog
- `stg_order_items`: Clean order line items
- `stg_stores`: Clean store locations
- `stg_inventory`: Clean inventory snapshots

### Dimensions
- `dim_customers`: SCD Type 2 - customer history
- `dim_products`: SCD Type 2 - product history
- `dim_stores`: SCD Type 2 - store history
- `dim_categories`: SCD Type 1 - category lookup

### Facts
- `fct_orders`: Order-level metrics
- `fct_order_items`: Line item-level metrics
- `fct_inventory_snapshots`: Periodic inventory snapshots

### Marts
- `mart_sales_summary`: Aggregated sales by dimensions
- `mart_customer_metrics`: Customer-level metrics and segmentation

## Running dbt

### Install dependencies
```bash
dbt deps
```

### Run models
```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_orders

# Run models with tag
dbt run --select tag:staging

# Run incremental models with full refresh
dbt run --select fct_orders --full-refresh
```

### Run tests
```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test --select stg_orders

# Run custom tests
dbt test --select test_type:data
```

### Generate documentation
```bash
dbt docs generate
dbt docs serve
```

## Environment Configuration

Set the `DBT_ENV` environment variable to switch between environments:
- `dev`: Development schema
- `qa`: QA schema
- `prod`: Production schema

```bash
export DBT_ENV=dev
dbt run --target dev
```

## SCD Implementation

- **SCD Type 2**: `dim_customers`, `dim_products`, `dim_stores`
  - Tracks full history with `valid_from`, `valid_to`, `current_flag`
  - Incremental processing closes old records and creates new ones

- **SCD Type 1**: `dim_categories`
  - Overwrites historical values

## Testing Strategy

1. **Built-in tests**: `unique`, `not_null`, `relationships`
2. **Custom SQL tests**: Business rule validations
3. **dbt_expectations**: Advanced data quality checks
4. **Test execution**: After each model build in Airflow

