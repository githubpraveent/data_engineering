# Testing Plan

## Overview

This document outlines the testing strategy for the retail data lake and data warehouse solution. Testing is performed at multiple levels to ensure data quality, pipeline reliability, and system correctness.

## Testing Levels

### 1. Unit Testing

#### SQL Transformation Testing

**Purpose**: Validate individual SQL transformations work correctly

**Approach**:
- Create test data sets with known inputs and expected outputs
- Execute transformation SQL against test data
- Compare actual results with expected results

**Example Test Cases**:
```sql
-- Test: Bronze to Silver POS transformation
-- Input: Raw POS record with known values
-- Expected: Staging record with cleaned/standardized values

INSERT INTO DEV_RAW.BRONZE.raw_pos (
    transaction_id, store_id, product_id, quantity, unit_price, total_amount
) VALUES (
    'TXN001', 'STORE01', 'PROD001', 2, 10.50, 21.00
);

-- Execute transformation
EXECUTE TASK DEV_STAGING.TASKS.task_bronze_to_silver_pos;

-- Verify result
SELECT 
    transaction_id,
    store_id,
    product_id,
    quantity,
    unit_price,
    total_amount,
    is_valid
FROM DEV_STAGING.SILVER.stg_pos
WHERE transaction_id = 'TXN001';

-- Expected: is_valid = TRUE, all fields cleaned/standardized
```

#### Stored Procedure Testing

**Purpose**: Validate stored procedures execute correctly

**Test Cases**:
1. SCD Type 2 dimension load with new records
2. SCD Type 2 dimension load with changed records
3. SCD Type 2 dimension load with no changes
4. SCD Type 1 dimension load (overwrite)
5. Fact table load with valid dimension keys
6. Fact table load with missing dimension keys (should handle gracefully)

**Example**:
```sql
-- Test SCD Type 2: New customer
INSERT INTO DEV_STAGING.SILVER.stg_customers (
    customer_id, first_name, last_name, email
) VALUES (
    'CUST001', 'John', 'Doe', 'john.doe@example.com'
);

CALL DEV_DW.DIMENSIONS.sp_load_dim_customer_scd_type2();

-- Verify: New record created with is_current = TRUE
SELECT * FROM DEV_DW.DIMENSIONS.dim_customer
WHERE customer_id = 'CUST001' AND is_current = TRUE;

-- Test SCD Type 2: Changed customer
UPDATE DEV_STAGING.SILVER.stg_customers
SET email = 'john.doe.new@example.com'
WHERE customer_id = 'CUST001';

CALL DEV_DW.DIMENSIONS.sp_load_dim_customer_scd_type2();

-- Verify: Old record closed, new record created
SELECT 
    customer_id,
    email,
    effective_from_date,
    effective_to_date,
    is_current
FROM DEV_DW.DIMENSIONS.dim_customer
WHERE customer_id = 'CUST001'
ORDER BY effective_from_date;
```

### 2. Integration Testing

#### End-to-End Pipeline Testing

**Purpose**: Validate complete data flow from ingestion to consumption

**Test Scenarios**:
1. **Full Pipeline Run**
   - Ingest test files
   - Transform Bronze → Silver → Gold
   - Validate final results

2. **Incremental Processing**
   - Load initial data
   - Load incremental changes
   - Verify only new/changed records processed

3. **Error Handling**
   - Invalid data in source
   - Missing dimension keys
   - Duplicate records

**Test Data Sets**:
- Small representative dataset (100-1000 records)
- Known data quality issues (nulls, invalid values)
- Edge cases (boundary values, special characters)

### 3. Data Quality Testing

#### Completeness Checks

**Tests**:
- No NULL values in critical fields
- All expected records present
- No missing date ranges

**SQL Example**:
```sql
SELECT 
    'Completeness Check' as test_type,
    COUNT(*) as total_rows,
    SUM(CASE WHEN transaction_id IS NULL THEN 1 ELSE 0 END) as null_transaction_id,
    SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as null_store_id
FROM DEV_STAGING.SILVER.stg_pos
WHERE created_at >= CURRENT_TIMESTAMP() - INTERVAL '24 hours';
```

#### Accuracy Checks

**Tests**:
- No negative amounts (where not expected)
- Calculations are correct (total = quantity * price - discount + tax)
- Values within expected ranges

**SQL Example**:
```sql
SELECT 
    'Accuracy Check' as test_type,
    COUNT(*) as calculation_errors
FROM DEV_STAGING.SILVER.stg_pos
WHERE ABS(total_amount - ((quantity * unit_price) - discount_amount + tax_amount)) > 0.01;
```

#### Consistency Checks

**Tests**:
- Referential integrity (all foreign keys valid)
- No duplicate transactions
- SCD Type 2: No overlapping effective dates
- SCD Type 2: Exactly one current record per business key

**SQL Example**:
```sql
-- Check referential integrity
SELECT 
    'Referential Integrity' as test_type,
    COUNT(*) as orphaned_records
FROM DEV_DW.FACTS.fact_sales fs
LEFT JOIN DEV_DW.DIMENSIONS.dim_product dp ON fs.product_key = dp.product_key
WHERE dp.product_key IS NULL;

-- Check SCD Type 2 consistency
SELECT 
    customer_id,
    COUNT(*) as current_record_count
FROM DEV_DW.DIMENSIONS.dim_customer
WHERE is_current = TRUE
GROUP BY customer_id
HAVING COUNT(*) != 1;
```

#### Timeliness Checks

**Tests**:
- Data loaded within expected timeframes
- No gaps in data loading
- Pipeline completes within SLA

**SQL Example**:
```sql
SELECT 
    'Timeliness Check' as test_type,
    MAX(load_timestamp) as latest_load,
    DATEDIFF(hour, MAX(load_timestamp), CURRENT_TIMESTAMP()) as hours_since_load
FROM DEV_RAW.BRONZE.raw_pos;
```

### 4. Performance Testing

#### Load Testing

**Purpose**: Validate system performance under expected load

**Test Scenarios**:
1. **Normal Load**: Typical daily data volume
2. **Peak Load**: Maximum expected data volume
3. **Sustained Load**: Continuous load over extended period

**Metrics to Monitor**:
- Query execution time
- Warehouse utilization
- Storage growth
- Cost per operation

#### Stress Testing

**Purpose**: Identify system limits and failure points

**Test Scenarios**:
1. Extremely large files
2. Very high data volumes
3. Concurrent pipeline executions
4. Resource contention

### 5. Regression Testing

#### Schema Change Testing

**Tests**:
- Adding new columns doesn't break existing transformations
- Changing data types handles existing data correctly
- Dropping columns doesn't cause errors in downstream processes

#### Code Change Testing

**Tests**:
- Modified transformations produce same results for unchanged data
- New transformations don't break existing ones
- Performance doesn't degrade

### 6. User Acceptance Testing (UAT)

#### Business Validation

**Tests**:
- Business users validate report results
- Data matches expectations from source systems
- Calculations match business logic
- Historical data is accurate

#### Data Reconciliation

**Tests**:
- Row counts match source systems
- Aggregated totals match source systems
- Dimension counts are correct

## Test Execution Strategy

### Automated Testing

1. **CI/CD Integration**
   - Run unit tests on every commit
   - Run integration tests on pull requests
   - Run full test suite before production deployment

2. **Scheduled Testing**
   - Daily data quality checks
   - Weekly performance tests
   - Monthly regression tests

### Manual Testing

1. **Pre-Deployment**
   - Manual validation of critical transformations
   - Business user sign-off on UAT results

2. **Post-Deployment**
   - Smoke tests after deployment
   - Validation of first production run

## Test Data Management

### Test Data Sets

1. **Synthetic Data**
   - Generated test data with known characteristics
   - Covers edge cases and boundary conditions

2. **Production Data Samples**
   - Anonymized production data samples
   - Representative of real-world scenarios

3. **Known Bad Data**
   - Data with intentional quality issues
   - Tests error handling and data quality checks

### Test Environment

- **Dev**: Primary testing environment
- **QA**: Pre-production validation
- **Prod Clone**: Production-like testing (using zero-copy clone)

## Test Results and Reporting

### Test Metrics

1. **Coverage Metrics**
   - Percentage of transformations tested
   - Percentage of stored procedures tested
   - Data quality check coverage

2. **Quality Metrics**
   - Number of test failures
   - Time to fix failures
   - Test execution time

3. **Business Metrics**
   - Data accuracy percentage
   - Pipeline reliability (uptime)
   - Data freshness (time to availability)

### Reporting

1. **Daily Reports**
   - Data quality summary
   - Pipeline execution status
   - Failed tests

2. **Weekly Reports**
   - Test coverage summary
   - Performance trends
   - Quality trends

3. **Monthly Reports**
   - Comprehensive test results
   - Test coverage analysis
   - Recommendations for improvement

## Test Maintenance

### Keeping Tests Current

1. **Update tests when schema changes**
2. **Update tests when business rules change**
3. **Add tests for new features**
4. **Remove obsolete tests**

### Test Documentation

1. **Document test cases**
2. **Document test data**
3. **Document expected results**
4. **Document test execution procedures**

## Continuous Improvement

### Test Process Improvement

1. **Regular review of test coverage**
2. **Identify gaps in testing**
3. **Improve test automation**
4. **Reduce manual testing effort**

### Learning from Failures

1. **Root cause analysis of test failures**
2. **Update tests to catch similar issues**
3. **Improve test data to cover edge cases**

## Appendix: Test Execution Checklist

### Pre-Deployment Testing

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Data quality checks pass
- [ ] Performance tests meet SLA
- [ ] UAT sign-off received
- [ ] Test documentation updated

### Post-Deployment Testing

- [ ] Smoke tests pass
- [ ] First production run successful
- [ ] Data quality checks pass
- [ ] Business validation complete
- [ ] Monitoring and alerts configured

### Ongoing Testing

- [ ] Daily data quality checks running
- [ ] Weekly performance tests scheduled
- [ ] Monthly regression tests executed
- [ ] Test coverage maintained
- [ ] Test results reviewed and acted upon

