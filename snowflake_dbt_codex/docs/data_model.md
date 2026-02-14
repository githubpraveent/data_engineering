# Healthcare Insurance and Claims Data Model

## Core Entities
- Member
- Provider
- Policy
- Plan
- Claim Header
- Claim Line
- Diagnosis
- Procedure
- Payment
- Adjustment

## Key Grain Definitions
- Member
- One row per member

- Provider
- One row per provider

- Policy
- One row per member policy enrollment period

- Claim Header
- One row per claim submission

- Claim Line
- One row per service line on a claim

## Dimensions
- dim_member
- dim_provider
- dim_policy
- dim_plan
- dim_diagnosis
- dim_procedure
- dim_date

## Facts
- fct_claim
- fct_claim_line
- fct_payment
- fct_adjustment

## Relationships
- Claim header to member via `member_id`
- Claim line to claim header via `claim_id`
- Claim line to provider via `provider_id`
- Claim line to diagnosis and procedure codes

## Reporting Outputs
- Claim summary by plan, provider, and service date
- Member utilization and risk indicators
- Payment and adjustment analytics
