{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'stores') }}
),

cleaned as (
    select
        -- Primary key
        cast(store_id as integer) as store_id,
        
        -- Attributes
        trim(store_name) as store_name,
        trim(address) as address,
        trim(city) as city,
        upper(trim(state)) as state,
        trim(zip_code) as zip_code,
        
        -- Timestamps
        cast(updated_at as timestamp) as updated_at,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where store_id is not null
)

select * from cleaned

