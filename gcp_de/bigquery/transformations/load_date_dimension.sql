-- Load Date Dimension Table
-- Populates the date dimension table with dates for analysis
-- Run this once to populate historical and future dates

DECLARE start_date DATE DEFAULT DATE('2020-01-01');
DECLARE end_date DATE DEFAULT DATE('2030-12-31');

INSERT INTO `{project_id}.{curated_dataset}.date_dimension`
SELECT
    date_id,
    EXTRACT(YEAR FROM date_id) AS year,
    EXTRACT(QUARTER FROM date_id) AS quarter,
    EXTRACT(MONTH FROM date_id) AS month,
    FORMAT_DATE('%B', date_id) AS month_name,
    EXTRACT(WEEK FROM date_id) AS week,
    EXTRACT(DAY FROM date_id) AS day_of_month,
    EXTRACT(DAYOFWEEK FROM date_id) AS day_of_week,
    FORMAT_DATE('%A', date_id) AS day_name,
    CASE WHEN EXTRACT(DAYOFWEEK FROM date_id) IN (1, 7) THEN TRUE ELSE FALSE END AS is_weekend,
    FALSE AS is_holiday,  -- Can be enhanced with holiday calendar
    CAST(NULL AS STRING) AS holiday_name,
    CASE 
        WHEN EXTRACT(MONTH FROM date_id) >= 4 THEN EXTRACT(YEAR FROM date_id)
        ELSE EXTRACT(YEAR FROM date_id) - 1
    END AS fiscal_year,
    CASE 
        WHEN EXTRACT(MONTH FROM date_id) IN (4, 5, 6) THEN 1
        WHEN EXTRACT(MONTH FROM date_id) IN (7, 8, 9) THEN 2
        WHEN EXTRACT(MONTH FROM date_id) IN (10, 11, 12) THEN 3
        ELSE 4
    END AS fiscal_quarter
FROM UNNEST(GENERATE_DATE_ARRAY(start_date, end_date)) AS date_id
WHERE date_id NOT IN (SELECT date_id FROM `{project_id}.{curated_dataset}.date_dimension`);

