-- Stored Procedure: Load Store Dimension (SCD Type 2)

CREATE OR ALTER PROCEDURE [dwh].[sp_load_store_dimension]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Update existing records that have changed (expire old records)
        UPDATE d
        SET 
            d.expiry_date = @processing_date,
            d.is_current = 0,
            d.updated_timestamp = GETDATE()
        FROM [dwh].[dim_store] d
        INNER JOIN [staging].[pos_events] s
            ON d.store_id = s.store_id
            AND d.is_current = 1
        WHERE s.processing_date = @processing_date;
        
        -- Insert new records for changed stores
        INSERT INTO [dwh].[dim_store] (
            [store_id],
            [store_name],
            [store_type],
            [address],
            [city],
            [state],
            [zip_code],
            [country],
            [geography_key],
            [manager_name],
            [opening_date],
            [effective_date],
            [expiry_date],
            [is_current],
            [created_timestamp],
            [updated_timestamp]
        )
        SELECT DISTINCT
            s.store_id,
            COALESCE(s.store_id, 'Unknown') AS store_name,
            NULL AS store_type,
            NULL AS address,
            NULL AS city,
            NULL AS state,
            NULL AS zip_code,
            NULL AS country,
            NULL AS geography_key,
            NULL AS manager_name,
            NULL AS opening_date,
            @processing_date AS effective_date,
            NULL AS expiry_date,
            1 AS is_current,
            GETDATE() AS created_timestamp,
            GETDATE() AS updated_timestamp
        FROM [staging].[pos_events] s
        LEFT JOIN [dwh].[dim_store] d
            ON s.store_id = d.store_id
            AND d.is_current = 1
        WHERE 
            d.store_key IS NULL
            AND s.processing_date = @processing_date
            AND s.store_id IS NOT NULL;
        
        COMMIT TRANSACTION;
        
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_processed,
            'Store Dimension Loaded Successfully' AS status
        FROM [dwh].[dim_store]
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

