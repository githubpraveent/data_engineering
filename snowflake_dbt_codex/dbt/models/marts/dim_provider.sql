select
  provider_id,
  provider_name,
  specialty,
  npi,
  updated_at
from {{ ref('stg_providers') }}
