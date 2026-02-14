{{ config(
    materialized='table',
    tags=['dimension', 'scd_type_2']
) }}

-- Dimension: Customers (SCD Type 2)
-- Maintains full history of customer changes

with staging as (
    select * from {{ ref('stg_customers') }}
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
        e.customer_id as existing_customer_id,
        case
            when e.customer_id is null then 'new'
            when s.updated_at > e.valid_from 
                and (
                    s.first_name != e.first_name
                    or s.last_name != e.last_name
                    or s.email != e.email
                    or s.address != e.address
                    or s.city != e.city
                    or s.state != e.state
                    or s.zip_code != e.zip_code
                ) then 'changed'
            else 'unchanged'
        end as change_type
    from staging s
    left join existing_dimension e
        on s.customer_id = e.customer_id
),

-- Close out old records
closed_records as (
    select
        customer_id,
        first_name,
        last_name,
        email,
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
        on e.customer_id = c.customer_id
    where c.change_type = 'changed'
      and e.current_flag = true
),

-- Create new/updated records
new_records as (
    select
        customer_id,
        first_name,
        last_name,
        email,
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
        on e.customer_id = c.customer_id
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
        customer_id,
        first_name,
        last_name,
        email,
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

