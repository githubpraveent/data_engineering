{{ config(
    materialized='view',
    tags=['staging']
) }}

with source as (
    select * from {{ source('raw_data', 'customers') }}
),

cleaned as (
    select
        -- Primary key
        cast(customer_id as integer) as customer_id,
        
        -- Attributes
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(trim(email)) as email,
        trim(address) as address,
        trim(city) as city,
        upper(trim(state)) as state,
        trim(zip_code) as zip_code,
        
        -- Timestamps
        cast(updated_at as timestamp) as updated_at,
        
        -- Metadata
        current_timestamp() as dbt_loaded_at
        
    from source
    where customer_id is not null
      and email is not null
)

select * from cleaned

