{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'products') }}
),

cleaned as (
    select
        -- Primary key
        cast(product_id as integer) as product_id,
        
        -- Attributes
        trim(product_name) as product_name,
        cast(category_id as integer) as category_id,
        
        -- Measures
        cast(price as decimal(10, 2)) as price,
        cast(cost as decimal(10, 2)) as cost,
        
        -- Calculated fields
        cast(price as decimal(10, 2)) - cast(cost as decimal(10, 2)) as margin,
        
        -- Timestamps
        cast(updated_at as timestamp) as updated_at,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where product_id is not null
      and price is not null
      and price >= 0
)

select * from cleaned

