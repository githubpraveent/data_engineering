{{ config(
    materialized='table',
    tags=['dimension', 'scd_type_2']
) }}

-- Dimension: Stores (SCD Type 2)
-- Maintains full history of store location changes

with staging as (
    select * from {{ ref('stg_stores') }}
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
        e.store_id as existing_store_id,
        case
            when e.store_id is null then 'new'
            when s.updated_at > e.valid_from 
                and (
                    s.store_name != e.store_name
                    or s.address != e.address
                    or s.city != e.city
                    or s.state != e.state
                    or s.zip_code != e.zip_code
                ) then 'changed'
            else 'unchanged'
        end as change_type
    from staging s
    left join existing_dimension e
        on s.store_id = e.store_id
),

-- Close out old records
closed_records as (
    select
        store_id,
        store_name,
        address,
        city,
        state,
        zip_code,
        valid_from,
        c.updated_at as valid_to,
        false as current_flag,
        dbt_loaded_at
    from existing_dimension e
    inner join changes c
        on e.store_id = c.store_id
    where c.change_type = 'changed'
      and e.current_flag = true
),

-- Create new/updated records
new_records as (
    select
        store_id,
        store_name,
        address,
        city,
        state,
        zip_code,
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
        on e.store_id = c.store_id
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
        store_id,
        store_name,
        address,
        city,
        state,
        zip_code,
        updated_at as valid_from,
        cast(null as timestamp) as valid_to,
        true as current_flag,
        dbt_loaded_at
    from staging
)

{% endif %}

select * from final

