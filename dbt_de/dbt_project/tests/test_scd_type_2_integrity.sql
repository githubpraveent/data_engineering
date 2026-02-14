-- Custom test: Validate SCD Type 2 dimension integrity
-- Ensures that for each business key, only one record has current_flag = true

select
    customer_id,
    count(*) as current_record_count
from {{ ref('dim_customers') }}
where current_flag = true
group by customer_id
having count(*) > 1

