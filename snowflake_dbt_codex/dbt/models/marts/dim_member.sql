select
  member_id,
  first_name,
  last_name,
  date_of_birth,
  gender,
  zip_code,
  plan_id,
  updated_at
from {{ ref('stg_members') }}
