{{ config(
    materialized='table',
    tags=['mart']
) }}

-- Mart: Sales Summary
-- Aggregated sales metrics by various dimensions

with orders as (
    select * from {{ ref('fct_orders') }}
),

order_items as (
    select * from {{ ref('fct_order_items') }}
),

dim_customers as (
    select * from {{ ref('dim_customers') }}
    where current_flag = true
),

dim_products as (
    select * from {{ ref('dim_products') }}
    where current_flag = true
),

dim_stores as (
    select * from {{ ref('dim_stores') }}
    where current_flag = true
),

dim_categories as (
    select * from {{ ref('dim_categories') }}
)

select
    -- Date dimensions
    oi.order_date,
    date_trunc('month', oi.order_date) as order_month,
    date_trunc('year', oi.order_date) as order_year,
    
    -- Store dimensions
    oi.store_id,
    ds.store_name,
    ds.city as store_city,
    ds.state as store_state,
    
    -- Product dimensions
    oi.product_id,
    dp.product_name,
    oi.category_id,
    dc.category_name,
    
    -- Customer dimensions
    o.customer_id,
    dim_c.first_name || ' ' || dim_c.last_name as customer_name,
    dim_c.state as customer_state,
    
    -- Aggregated measures
    count(distinct o.order_id) as order_count,
    count(distinct oi.order_item_id) as line_item_count,
    sum(oi.quantity) as total_quantity_sold,
    sum(oi.line_total) as total_revenue,
    sum(oi.total_cost) as total_cost,
    sum(oi.profit) as total_profit,
    
    -- Calculated metrics
    avg(oi.line_total) as avg_line_total,
    avg(oi.quantity) as avg_quantity_per_line,
    sum(oi.profit) / nullif(sum(oi.line_total), 0) as profit_margin_pct

from order_items oi
inner join orders o
    on oi.order_id = o.order_id
left join dim_stores ds
    on oi.store_id = ds.store_id
left join dim_products dp
    on oi.product_id = dp.product_id
left join dim_categories dc
    on oi.category_id = dc.category_id
left join dim_customers dim_c
    on o.customer_id = dim_c.customer_id

group by
    oi.order_date,
    date_trunc('month', oi.order_date),
    date_trunc('year', oi.order_date),
    oi.store_id,
    ds.store_name,
    ds.city,
    ds.state,
    oi.product_id,
    dp.product_name,
    oi.category_id,
    dc.category_name,
    o.customer_id,
    dim_c.first_name,
    dim_c.last_name,
    dim_c.state

