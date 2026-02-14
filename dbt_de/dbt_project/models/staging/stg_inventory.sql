{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'inventory') }}
),

cleaned as (
    select
        -- Primary key
        cast(inventory_id as integer) as inventory_id,
        
        -- Foreign keys
        cast(store_id as integer) as store_id,
        cast(product_id as integer) as product_id,
        
        -- Measures
        cast(quantity_on_hand as integer) as quantity_on_hand,
        
        -- Dates
        cast(snapshot_date as date) as snapshot_date,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where store_id is not null
      and product_id is not null
      and snapshot_date is not null
)

select * from cleaned

