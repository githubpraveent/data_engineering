-- Stored Procedure: Load Date Dimension
-- This procedure populates the date dimension table (static, one-time load)

CREATE OR ALTER PROCEDURE [dwh].[sp_load_date_dimension]
    @start_date DATE = '2020-01-01',
    @end_date DATE = '2030-12-31'
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Generate dates using a numbers table approach (more efficient for Synapse)
        DECLARE @date_count INT = DATEDIFF(DAY, @start_date, @end_date) + 1;
        
        -- Use a numbers table to generate dates
        WITH Numbers AS (
            SELECT ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) - 1 AS n
            FROM sys.objects o1
            CROSS JOIN sys.objects o2
            CROSS JOIN sys.objects o3
        ),
        DateSeries AS (
            SELECT TOP (@date_count)
                DATEADD(DAY, n, @start_date) AS date_value
            FROM Numbers
            WHERE DATEADD(DAY, n, @start_date) <= @end_date
        )
        INSERT INTO [dwh].[dim_date] (
            [date_key],
            [date],
            [day],
            [month],
            [year],
            [quarter],
            [week],
            [day_of_week],
            [day_name],
            [month_name],
            [is_weekend],
            [is_holiday]
        )
        SELECT 
            CAST(FORMAT(date_value, 'yyyyMMdd') AS INT) AS date_key,
            date_value AS date,
            DAY(date_value) AS day,
            MONTH(date_value) AS month,
            YEAR(date_value) AS year,
            DATEPART(QUARTER, date_value) AS quarter,
            DATEPART(WEEK, date_value) AS week,
            DATEPART(WEEKDAY, date_value) AS day_of_week,
            DATENAME(WEEKDAY, date_value) AS day_name,
            DATENAME(MONTH, date_value) AS month_name,
            CASE WHEN DATEPART(WEEKDAY, date_value) IN (1, 7) THEN 1 ELSE 0 END AS is_weekend,
            0 AS is_holiday  -- Placeholder, add holiday logic as needed
        FROM DateSeries
        WHERE NOT EXISTS (
            SELECT 1 
            FROM [dwh].[dim_date] d
            WHERE d.date = date_value
        )
        OPTION (MAXRECURSION 0);
        
        COMMIT TRANSACTION;
        
        -- Return summary
        SELECT 
            COUNT(*) AS total_dates,
            MIN(date) AS min_date,
            MAX(date) AS max_date,
            'Date Dimension Loaded Successfully' AS status
        FROM [dwh].[dim_date];
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        -- Log error
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO

