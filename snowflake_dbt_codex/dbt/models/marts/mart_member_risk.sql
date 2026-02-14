with claims as (
  select * from {{ ref('int_claims_enriched') }}
)
select
  member_id,
  count(distinct claim_id) as claim_count,
  sum(total_allowed_amount) as allowed_amount,
  sum(total_paid_amount) as paid_amount
from claims
group by member_id
