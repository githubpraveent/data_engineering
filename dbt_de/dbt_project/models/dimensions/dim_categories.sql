{{ config(
    materialized='table',
    tags=['dimension', 'scd_type_1']
) }}

-- Dimension: Categories (SCD Type 1)
-- Overwrites historical values - no history tracking needed

with staging as (
    select distinct
        category_id,
        'Category ' || category_id as category_name,  -- Placeholder, replace with actual category data
        current_timestamp() as dbt_loaded_at
    from {{ ref('stg_products') }}
    where category_id is not null
)

select * from staging

