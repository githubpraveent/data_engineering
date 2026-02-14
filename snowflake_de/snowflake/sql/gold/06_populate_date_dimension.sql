-- ============================================================================
-- Populate Date Dimension
-- Creates a comprehensive date dimension for time-based analysis
-- ============================================================================

USE DATABASE DEV_DW;
USE SCHEMA DIMENSIONS;

-- ============================================================================
-- Stored Procedure: Populate Date Dimension
-- ============================================================================

CREATE OR REPLACE PROCEDURE sp_populate_date_dimension(
    start_date DATE,
    end_date DATE
)
RETURNS VARCHAR
LANGUAGE SQL
AS
$$
BEGIN
    INSERT INTO dim_date (
        date_key,
        date_value,
        day_of_week,
        day_name,
        day_of_month,
        day_of_year,
        week_of_year,
        week_start_date,
        week_end_date,
        month_number,
        month_name,
        month_abbreviation,
        month_start_date,
        month_end_date,
        quarter_number,
        quarter_name,
        quarter_start_date,
        quarter_end_date,
        year_number,
        year_start_date,
        year_end_date,
        fiscal_year,
        fiscal_quarter,
        fiscal_month,
        is_weekend,
        is_holiday,
        holiday_name,
        is_business_day,
        created_at
    )
    WITH date_series AS (
        SELECT
            DATEADD(day, seq4(), :start_date) as date_value
        FROM TABLE(GENERATOR(ROWCOUNT => DATEDIFF(day, :start_date, :end_date) + 1))
    )
    SELECT
        -- Date key (YYYYMMDD format)
        TO_NUMBER(TO_CHAR(date_value, 'YYYYMMDD')) as date_key,
        date_value,
        
        -- Day attributes
        DAYOFWEEK(date_value) as day_of_week,
        DAYNAME(date_value) as day_name,
        DAY(date_value) as day_of_month,
        DAYOFYEAR(date_value) as day_of_year,
        
        -- Week attributes
        WEEK(date_value) as week_of_year,
        DATE_TRUNC('week', date_value) as week_start_date,
        DATEADD(day, 6, DATE_TRUNC('week', date_value)) as week_end_date,
        
        -- Month attributes
        MONTH(date_value) as month_number,
        MONTHNAME(date_value) as month_name,
        SUBSTR(MONTHNAME(date_value), 1, 3) as month_abbreviation,
        DATE_TRUNC('month', date_value) as month_start_date,
        LAST_DAY(date_value) as month_end_date,
        
        -- Quarter attributes
        QUARTER(date_value) as quarter_number,
        'Q' || QUARTER(date_value) as quarter_name,
        DATE_TRUNC('quarter', date_value) as quarter_start_date,
        LAST_DAY(DATEADD(month, 2, DATE_TRUNC('quarter', date_value))) as quarter_end_date,
        
        -- Year attributes
        YEAR(date_value) as year_number,
        DATE_TRUNC('year', date_value) as year_start_date,
        LAST_DAY(DATEADD(month, 11, DATE_TRUNC('year', date_value))) as year_end_date,
        
        -- Fiscal attributes (assuming fiscal year starts in October)
        CASE
            WHEN MONTH(date_value) >= 10 THEN YEAR(date_value) + 1
            ELSE YEAR(date_value)
        END as fiscal_year,
        CASE
            WHEN MONTH(date_value) IN (10, 11, 12) THEN 1
            WHEN MONTH(date_value) IN (1, 2, 3) THEN 2
            WHEN MONTH(date_value) IN (4, 5, 6) THEN 3
            WHEN MONTH(date_value) IN (7, 8, 9) THEN 4
        END as fiscal_quarter,
        CASE
            WHEN MONTH(date_value) >= 10 THEN MONTH(date_value) - 9
            ELSE MONTH(date_value) + 3
        END as fiscal_month,
        
        -- Flags
        CASE WHEN DAYOFWEEK(date_value) IN (0, 6) THEN TRUE ELSE FALSE END as is_weekend,
        FALSE as is_holiday,  -- Can be enhanced with holiday calendar
        NULL as holiday_name,
        CASE WHEN DAYOFWEEK(date_value) NOT IN (0, 6) THEN TRUE ELSE FALSE END as is_business_day,
        
        CURRENT_TIMESTAMP() as created_at
    FROM date_series
    WHERE date_value NOT IN (SELECT date_value FROM dim_date);
    
    RETURN 'SUCCESS: Date dimension populated from ' || :start_date || ' to ' || :end_date;
END;
$$;

-- ============================================================================
-- Populate Date Dimension (Example: 5 years of data)
-- ============================================================================

CALL sp_populate_date_dimension('2020-01-01'::DATE, '2025-12-31'::DATE);

-- ============================================================================
-- Populate Time Dimension
-- ============================================================================

INSERT INTO dim_time (
    time_key,
    time_value,
    hour_24,
    hour_12,
    minute,
    second,
    am_pm,
    hour_of_day,
    time_period,
    created_at
)
SELECT
    -- Time key (HHMMSS format)
    (HOUR(time_value) * 10000 + MINUTE(time_value) * 100 + SECOND(time_value)) as time_key,
    time_value,
    HOUR(time_value) as hour_24,
    CASE
        WHEN HOUR(time_value) = 0 THEN 12
        WHEN HOUR(time_value) <= 12 THEN HOUR(time_value)
        ELSE HOUR(time_value) - 12
    END as hour_12,
    MINUTE(time_value) as minute,
    SECOND(time_value) as second,
    CASE WHEN HOUR(time_value) < 12 THEN 'AM' ELSE 'PM' END as am_pm,
    CASE
        WHEN HOUR(time_value) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN HOUR(time_value) BETWEEN 12 AND 17 THEN 'Afternoon'
        WHEN HOUR(time_value) BETWEEN 18 AND 21 THEN 'Evening'
        ELSE 'Night'
    END as hour_of_day,
    CASE
        WHEN HOUR(time_value) BETWEEN 0 AND 5 THEN 'Early Morning'
        WHEN HOUR(time_value) BETWEEN 6 AND 11 THEN 'Morning'
        WHEN HOUR(time_value) BETWEEN 12 AND 13 THEN 'Midday'
        WHEN HOUR(time_value) BETWEEN 14 AND 17 THEN 'Afternoon'
        WHEN HOUR(time_value) BETWEEN 18 AND 21 THEN 'Evening'
        ELSE 'Night'
    END as time_period,
    CURRENT_TIMESTAMP() as created_at
FROM (
    SELECT TIME_FROM_PARTS(
        seq1() % 24,
        seq2() % 60,
        seq3() % 60
    ) as time_value
    FROM TABLE(GENERATOR(ROWCOUNT => 86400))  -- All seconds in a day
    WHERE seq1() < 24 AND seq2() < 60 AND seq3() < 60
)
WHERE time_value NOT IN (SELECT time_value FROM dim_time);

-- ============================================================================
-- Grant Execute Permission
-- ============================================================================

GRANT USAGE ON PROCEDURE sp_populate_date_dimension(DATE, DATE) TO ROLE DATA_ENGINEER;

