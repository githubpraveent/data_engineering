select
  c.claim_id,
  c.member_id,
  c.provider_id,
  c.claim_status,
  c.claim_type,
  c.total_allowed_amount,
  c.total_paid_amount,
  c.line_allowed_amount,
  c.line_paid_amount,
  c.total_units,
  c.service_start_date,
  c.service_end_date,
  c.updated_at
from {{ ref('int_claims_enriched') }} c
