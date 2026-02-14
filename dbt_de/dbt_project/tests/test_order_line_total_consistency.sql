-- Custom test: Validate that line_total equals quantity * unit_price
-- This is a data quality check for order items

select
    order_item_id,
    line_total,
    quantity * unit_price as calculated_total,
    abs(line_total - (quantity * unit_price)) as difference
from {{ ref('stg_order_items') }}
where abs(line_total - (quantity * unit_price)) > 0.01  -- Allow for rounding differences

