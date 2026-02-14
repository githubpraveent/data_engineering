{{ config(
    materialized='incremental',
    unique_key='order_item_id',
    on_schema_change='append_new_columns',
    tags=['fact']
) }}

-- Fact: Order Items
-- Transactional fact table for order line item-level metrics

with order_items_enriched as (
    select * from {{ ref('int_order_items_enriched') }}
),

-- Get current dimension records (for SCD Type 2)
dim_customers as (
    select
        customer_id
    from {{ ref('dim_customers') }}
    where current_flag = true
),

dim_products as (
    select
        product_id
    from {{ ref('dim_products') }}
    where current_flag = true
),

dim_stores as (
    select
        store_id
    from {{ ref('dim_stores') }}
    where current_flag = true
)

select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.order_date,
    
    -- Measures
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    oi.total_cost,
    oi.profit,
    oi.line_item_pct_of_order,
    
    -- Product context
    oi.product_name,
    oi.category_id,
    oi.current_product_price,
    
    -- Metadata
    current_timestamp() as dbt_loaded_at

from order_items_enriched oi
left join dim_customers dc
    on oi.customer_id = dc.customer_id
left join dim_products dp
    on oi.product_id = dp.product_id
left join dim_stores ds
    on oi.store_id = ds.store_id

{% if is_incremental() %}
    -- Only process new or updated order items
    where oi.order_date >= (select max(order_date) from {{ this }})
       or oi.order_item_id not in (select order_item_id from {{ this }})
{% endif %}

