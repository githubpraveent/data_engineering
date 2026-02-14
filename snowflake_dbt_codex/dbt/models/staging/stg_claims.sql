select
  claim_id,
  member_id,
  provider_id,
  claim_status,
  claim_type,
  total_allowed_amount,
  total_paid_amount,
  service_start_date,
  service_end_date,
  updated_at
from {{ source('raw', 'claims') }}
