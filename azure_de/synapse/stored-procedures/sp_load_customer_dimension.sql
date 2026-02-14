-- Stored Procedure: Load Customer Dimension (SCD Type 2)
-- This procedure implements SCD Type 2 logic for customer dimension

CREATE OR ALTER PROCEDURE [dwh].[sp_load_customer_dimension]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default to today if not provided
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Step 1: Update existing records that have changed (expire old records)
        UPDATE d
        SET 
            d.expiry_date = @processing_date,
            d.is_current = 0,
            d.updated_timestamp = GETDATE()
        FROM [dwh].[dim_customer] d
        INNER JOIN [staging].[pos_events] s
            ON d.customer_id = s.customer_id
            AND d.is_current = 1
        WHERE 
            -- Check for changes in key attributes
            (d.customer_name <> s.customer_id OR d.customer_name IS NULL)
            OR (d.email <> s.customer_id OR d.email IS NULL)
            -- Add more change detection logic as needed
            AND s.processing_date = @processing_date;
        
        -- Step 2: Insert new records for changed customers
        INSERT INTO [dwh].[dim_customer] (
            [customer_id],
            [customer_name],
            [email],
            [phone],
            [address],
            [city],
            [state],
            [zip_code],
            [country],
            [customer_segment],
            [effective_date],
            [expiry_date],
            [is_current],
            [created_timestamp],
            [updated_timestamp]
        )
        SELECT DISTINCT
            s.customer_id,
            COALESCE(s.customer_id, 'Unknown') AS customer_name,  -- Placeholder, adjust based on actual source
            NULL AS email,  -- Placeholder
            NULL AS phone,
            NULL AS address,
            NULL AS city,
            NULL AS state,
            NULL AS zip_code,
            NULL AS country,
            NULL AS customer_segment,
            @processing_date AS effective_date,
            NULL AS expiry_date,
            1 AS is_current,
            GETDATE() AS created_timestamp,
            GETDATE() AS updated_timestamp
        FROM [staging].[pos_events] s
        LEFT JOIN [dwh].[dim_customer] d
            ON s.customer_id = d.customer_id
            AND d.is_current = 1
        WHERE 
            d.customer_key IS NULL  -- New customer
            AND s.processing_date = @processing_date
            AND s.customer_id IS NOT NULL;
        
        -- Step 3: Insert new customers that don't exist at all
        INSERT INTO [dwh].[dim_customer] (
            [customer_id],
            [customer_name],
            [email],
            [phone],
            [address],
            [city],
            [state],
            [zip_code],
            [country],
            [customer_segment],
            [effective_date],
            [expiry_date],
            [is_current],
            [created_timestamp],
            [updated_timestamp]
        )
        SELECT DISTINCT
            s.customer_id,
            COALESCE(s.customer_id, 'Unknown') AS customer_name,
            NULL AS email,
            NULL AS phone,
            NULL AS address,
            NULL AS city,
            NULL AS state,
            NULL AS zip_code,
            NULL AS country,
            NULL AS customer_segment,
            @processing_date AS effective_date,
            NULL AS expiry_date,
            1 AS is_current,
            GETDATE() AS created_timestamp,
            GETDATE() AS updated_timestamp
        FROM [staging].[pos_events] s
        WHERE 
            s.customer_id NOT IN (SELECT customer_id FROM [dwh].[dim_customer])
            AND s.processing_date = @processing_date
            AND s.customer_id IS NOT NULL;
        
        COMMIT TRANSACTION;
        
        -- Return summary
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_processed,
            'Customer Dimension Loaded Successfully' AS status
        FROM [dwh].[dim_customer]
        WHERE effective_date = @processing_date;
        
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

