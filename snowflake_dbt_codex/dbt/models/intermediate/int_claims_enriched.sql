with claims as (
  select * from {{ ref('stg_claims') }}
),
lines as (
  select * from {{ ref('stg_claim_lines') }}
),
agg_lines as (
  select
    claim_id,
    sum(allowed_amount) as line_allowed_amount,
    sum(paid_amount) as line_paid_amount,
    sum(units) as total_units
  from lines
  group by claim_id
)
select
  c.claim_id,
  c.member_id,
  c.provider_id,
  c.claim_status,
  c.claim_type,
  c.total_allowed_amount,
  c.total_paid_amount,
  c.service_start_date,
  c.service_end_date,
  coalesce(a.line_allowed_amount, 0) as line_allowed_amount,
  coalesce(a.line_paid_amount, 0) as line_paid_amount,
  coalesce(a.total_units, 0) as total_units,
  c.updated_at
from claims c
left join agg_lines a
  on c.claim_id = a.claim_id
