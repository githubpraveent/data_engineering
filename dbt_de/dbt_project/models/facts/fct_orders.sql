{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='append_new_columns',
    tags=['fact']
) }}

-- Fact: Orders
-- Transactional fact table for order-level metrics

with order_items_enriched as (
    select * from {{ ref('int_order_items_enriched') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

-- Aggregate order items to order level
order_aggregates as (
    select
        order_id,
        count(distinct product_id) as distinct_product_count,
        sum(quantity) as total_quantity,
        sum(line_total) as calculated_total_amount,
        sum(total_cost) as total_cost,
        sum(profit) as total_profit
    from order_items_enriched
    group by order_id
)

select
    o.order_id,
    o.customer_id,
    o.store_id,
    o.order_date,
    o.status as order_status,
    o.total_amount,
    
    -- Aggregated metrics
    coalesce(oa.distinct_product_count, 0) as distinct_product_count,
    coalesce(oa.total_quantity, 0) as total_quantity,
    coalesce(oa.total_cost, 0) as total_cost,
    coalesce(oa.total_profit, 0) as total_profit,
    
    -- Calculated metrics
    o.total_amount - coalesce(oa.total_cost, 0) as profit_margin,
    case
        when o.total_amount > 0
        then (o.total_amount - coalesce(oa.total_cost, 0)) / o.total_amount
        else 0
    end as profit_margin_pct,
    
    -- Metadata
    current_timestamp() as dbt_loaded_at

from orders o
left join order_aggregates oa
    on o.order_id = oa.order_id

{% if is_incremental() %}
    -- Only process new or updated orders
    where o.order_date >= (select max(order_date) from {{ this }})
       or o.order_id not in (select order_id from {{ this }})
{% endif %}

