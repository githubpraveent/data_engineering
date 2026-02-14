{{ config(
    materialized='incremental',
    unique_key='inventory_snapshot_key',
    on_schema_change='append_new_columns',
    tags=['fact', 'snapshot']
) }}

-- Fact: Inventory Snapshots
-- Periodic snapshot fact table for inventory levels

with inventory as (
    select * from {{ ref('stg_inventory') }}
),

dim_products as (
    select
        product_id
    from {{ ref('dim_products') }}
    where current_flag = true
),

dim_stores as (
    select
        store_id
    from {{ ref('dim_stores') }}
    where current_flag = true
)

select
    -- Composite key
    {{ dbt_utils.surrogate_key(['i.store_id', 'i.product_id', 'i.snapshot_date']) }} as inventory_snapshot_key,
    
    i.store_id,
    i.product_id,
    i.snapshot_date,
    
    -- Measures
    i.quantity_on_hand,
    
    -- Metadata
    current_timestamp() as dbt_loaded_at

from inventory i
left join dim_stores ds
    on i.store_id = ds.store_id
left join dim_products dp
    on i.product_id = dp.product_id

{% if is_incremental() %}
    -- Only process new snapshots
    where i.snapshot_date >= (select max(snapshot_date) from {{ this }})
       or {{ dbt_utils.surrogate_key(['i.store_id', 'i.product_id', 'i.snapshot_date']) }} 
          not in (select inventory_snapshot_key from {{ this }})
{% endif %}

