select
  claim_line_id,
  claim_id,
  procedure_code,
  diagnosis_code,
  units,
  allowed_amount,
  paid_amount,
  service_date,
  updated_at
from {{ source('raw', 'claim_lines') }}
