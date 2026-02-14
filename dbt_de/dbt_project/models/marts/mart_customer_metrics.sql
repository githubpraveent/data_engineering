{{ config(
    materialized='table',
    tags=['mart']
) }}

-- Mart: Customer Metrics
-- Customer-level aggregated metrics for analytics

with orders as (
    select * from {{ ref('fct_orders') }}
),

dim_customers as (
    select * from {{ ref('dim_customers') }}
    where current_flag = true
)

select
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.city,
    c.state,
    
    -- Order metrics
    count(distinct o.order_id) as total_orders,
    min(o.order_date) as first_order_date,
    max(o.order_date) as last_order_date,
    datediff('day', min(o.order_date), max(o.order_date)) as customer_lifetime_days,
    
    -- Revenue metrics
    sum(o.total_amount) as total_revenue,
    avg(o.total_amount) as avg_order_value,
    sum(o.total_profit) as total_profit,
    
    -- Frequency metrics
    case
        when datediff('day', min(o.order_date), max(o.order_date)) > 0
        then count(distinct o.order_id)::float / datediff('day', min(o.order_date), max(o.order_date))
        else 0
    end as orders_per_day,
    
    -- Recency
    datediff('day', max(o.order_date), current_date()) as days_since_last_order,
    
    -- Customer segment (simple RFM-like)
    case
        when sum(o.total_amount) >= 1000 and count(distinct o.order_id) >= 5 then 'VIP'
        when sum(o.total_amount) >= 500 then 'High Value'
        when count(distinct o.order_id) >= 3 then 'Frequent'
        else 'Standard'
    end as customer_segment

from dim_customers c
left join orders o
    on c.customer_id = o.customer_id

group by
    c.customer_id,
    c.first_name,
    c.last_name,
    c.email,
    c.city,
    c.state

