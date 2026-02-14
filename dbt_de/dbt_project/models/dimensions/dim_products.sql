{{ config(
    materialized='table',
    tags=['dimension', 'scd_type_2']
) }}

-- Dimension: Products (SCD Type 2)
-- Maintains full history of product changes (price, cost, name, etc.)

with staging as (
    select * from {{ ref('stg_products') }}
),

{% if is_incremental() %}

existing_dimension as (
    select * from {{ this }}
    where current_flag = true
),

-- Identify changed records
changes as (
    select
        s.*,
        e.product_id as existing_product_id,
        case
            when e.product_id is null then 'new'
            when s.updated_at > e.valid_from 
                and (
                    s.product_name != e.product_name
                    or s.category_id != e.category_id
                    or s.price != e.price
                    or s.cost != e.cost
                ) then 'changed'
            else 'unchanged'
        end as change_type
    from staging s
    left join existing_dimension e
        on s.product_id = e.product_id
),

-- Close out old records
closed_records as (
    select
        product_id,
        product_name,
        category_id,
        price,
        cost,
        margin,
        valid_from,
        c.updated_at as valid_to,
        false as current_flag,
        dbt_loaded_at
    from existing_dimension e
    inner join changes c
        on e.product_id = c.product_id
    where c.change_type = 'changed'
      and e.current_flag = true
),

-- Create new/updated records
new_records as (
    select
        product_id,
        product_name,
        category_id,
        price,
        cost,
        margin,
        updated_at as valid_from,
        cast(null as timestamp) as valid_to,
        true as current_flag,
        dbt_loaded_at
    from changes
    where change_type in ('new', 'changed')
),

-- Unchanged records
unchanged_records as (
    select
        e.*
    from existing_dimension e
    inner join changes c
        on e.product_id = c.product_id
    where c.change_type = 'unchanged'
),

final as (
    select * from unchanged_records
    union all
    select * from closed_records
    union all
    select * from new_records
)

{% else %}

-- Initial load
final as (
    select
        product_id,
        product_name,
        category_id,
        price,
        cost,
        margin,
        updated_at as valid_from,
        cast(null as timestamp) as valid_to,
        true as current_flag,
        dbt_loaded_at
    from staging
)

{% endif %}

select * from final

