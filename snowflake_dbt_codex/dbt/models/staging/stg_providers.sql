select
  provider_id,
  provider_name,
  specialty,
  npi,
  updated_at
from {{ source('raw', 'providers') }}
