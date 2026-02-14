{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'orders') }}
),

cleaned as (
    select
        -- Primary key
        cast(order_id as integer) as order_id,
        
        -- Foreign keys
        cast(customer_id as integer) as customer_id,
        cast(store_id as integer) as store_id,
        
        -- Dates
        cast(order_date as date) as order_date,
        
        -- Measures
        cast(total_amount as decimal(10, 2)) as total_amount,
        
        -- Attributes
        upper(trim(status)) as status,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where order_id is not null
)

select * from cleaned

