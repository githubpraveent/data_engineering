-- Stored Procedure: Load Geography Dimension (SCD Type 2)

CREATE OR ALTER PROCEDURE [dwh].[sp_load_geography_dimension]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Insert new geography records from staging
        INSERT INTO [dwh].[dim_geography] (
            [city],
            [state],
            [zip_code],
            [country],
            [region],
            [latitude],
            [longitude],
            [effective_date],
            [expiry_date],
            [is_current],
            [created_timestamp],
            [updated_timestamp]
        )
        SELECT DISTINCT
            NULL AS city,  -- Placeholder, adjust based on actual source
            NULL AS state,
            NULL AS zip_code,
            'USA' AS country,  -- Placeholder
            NULL AS region,
            NULL AS latitude,
            NULL AS longitude,
            @processing_date AS effective_date,
            NULL AS expiry_date,
            1 AS is_current,
            GETDATE() AS created_timestamp,
            GETDATE() AS updated_timestamp
        FROM [staging].[pos_events] s
        WHERE s.processing_date = @processing_date
            AND NOT EXISTS (
                SELECT 1 
                FROM [dwh].[dim_geography] g
                WHERE g.is_current = 1
            );
        
        COMMIT TRANSACTION;
        
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_processed,
            'Geography Dimension Loaded Successfully' AS status
        FROM [dwh].[dim_geography]
        WHERE effective_date = @processing_date;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
        
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO

