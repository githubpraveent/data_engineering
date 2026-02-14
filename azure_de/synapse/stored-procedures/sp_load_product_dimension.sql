-- Stored Procedure: Load Product Dimension (SCD Type 1)
-- This procedure implements SCD Type 1 logic (overwrite) for product dimension

CREATE OR ALTER PROCEDURE [dwh].[sp_load_product_dimension]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default to today if not provided
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Step 1: Update existing products (SCD Type 1 - overwrite)
        UPDATE d
        SET 
            d.product_name = COALESCE(s.product_id, 'Unknown'),  -- Placeholder, adjust based on actual source
            d.product_category = NULL,  -- Placeholder
            d.product_subcategory = NULL,  -- Placeholder
            d.brand = NULL,  -- Placeholder
            d.unit_price = s.price,
            d.cost = NULL,  -- Placeholder
            d.supplier_id = NULL,  -- Placeholder
            d.updated_timestamp = GETDATE()
        FROM [dwh].[dim_product] d
        INNER JOIN [staging].[pos_events] s
            ON d.product_id = s.product_id
        WHERE s.processing_date = @processing_date;
        
        -- Step 2: Insert new products
        INSERT INTO [dwh].[dim_product] (
            [product_id],
            [product_name],
            [product_category],
            [product_subcategory],
            [brand],
            [unit_price],
            [cost],
            [supplier_id],
            [created_timestamp],
            [updated_timestamp]
        )
        SELECT DISTINCT
            s.product_id,
            COALESCE(s.product_id, 'Unknown') AS product_name,
            NULL AS product_category,
            NULL AS product_subcategory,
            NULL AS brand,
            AVG(s.price) AS unit_price,  -- Average price if multiple prices
            NULL AS cost,
            NULL AS supplier_id,
            GETDATE() AS created_timestamp,
            GETDATE() AS updated_timestamp
        FROM [staging].[pos_events] s
        LEFT JOIN [dwh].[dim_product] d
            ON s.product_id = d.product_id
        WHERE 
            d.product_key IS NULL  -- New product
            AND s.processing_date = @processing_date
            AND s.product_id IS NOT NULL
        GROUP BY s.product_id;
        
        COMMIT TRANSACTION;
        
        -- Return summary
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_processed,
            'Product Dimension Loaded Successfully' AS status
        FROM [dwh].[dim_product]
        WHERE updated_timestamp >= CAST(@processing_date AS DATETIME2);
        
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

