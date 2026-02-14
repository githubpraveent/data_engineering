{{ config(
    materialized='view',
    tags=['intermediate']
) }}

-- Intermediate model: Enriches order items with product and order details
-- This model prepares data for fact table creation

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
),

products as (
    select * from {{ ref('stg_products') }}
)

select
    oi.order_item_id,
    oi.order_id,
    oi.product_id,
    oi.quantity,
    oi.unit_price,
    oi.line_total,
    
    -- Order context
    o.order_date,
    o.customer_id,
    o.store_id,
    o.status as order_status,
    
    -- Product context
    p.product_name,
    p.category_id,
    p.price as current_product_price,
    p.cost as product_cost,
    
    -- Calculated fields
    oi.quantity * p.cost as total_cost,
    oi.line_total - (oi.quantity * p.cost) as profit,
    oi.line_total / o.total_amount as line_item_pct_of_order
    
from order_items oi
inner join orders o
    on oi.order_id = o.order_id
inner join products p
    on oi.product_id = p.product_id

