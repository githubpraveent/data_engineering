{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'order_items') }}
),

cleaned as (
    select
        -- Primary key
        cast(order_item_id as integer) as order_item_id,
        
        -- Foreign keys
        cast(order_id as integer) as order_id,
        cast(product_id as integer) as product_id,
        
        -- Measures
        cast(quantity as integer) as quantity,
        cast(unit_price as decimal(10, 2)) as unit_price,
        cast(line_total as decimal(10, 2)) as line_total,
        
        -- Calculated validation
        cast(quantity as integer) * cast(unit_price as decimal(10, 2)) as calculated_line_total,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where order_item_id is not null
      and order_id is not null
      and product_id is not null
      and quantity > 0
)

select * from cleaned

