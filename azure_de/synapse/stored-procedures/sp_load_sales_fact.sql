-- Stored Procedure: Load Sales Fact Table
-- This procedure loads sales fact data from Gold layer (via staging) into the warehouse

CREATE OR ALTER PROCEDURE [dwh].[sp_load_sales_fact]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Default to today if not provided
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Insert sales fact records
        -- Note: This assumes data is already in staging from Gold layer
        INSERT INTO [dwh].[fact_sales] (
            [date_key],
            [customer_key],
            [product_key],
            [store_key],
            [geography_key],
            [transaction_id],
            [transaction_timestamp],
            [quantity],
            [unit_price],
            [line_total],
            [discount_amount],
            [tax_amount],
            [net_amount],
            [created_timestamp]
        )
        SELECT 
            dd.date_key,
            dc.customer_key,
            dp.product_key,
            ds.store_key,
            dg.geography_key,
            s.transaction_id,
            s.transaction_timestamp,
            s.quantity,
            s.price AS unit_price,
            s.line_total,
            COALESCE(s.discount_amount, 0) AS discount_amount,
            COALESCE(s.tax_amount, 0) AS tax_amount,
            s.line_total - COALESCE(s.discount_amount, 0) + COALESCE(s.tax_amount, 0) AS net_amount,
            GETDATE() AS created_timestamp
        FROM [staging].[pos_events] s
        INNER JOIN [dwh].[dim_date] dd
            ON CAST(s.transaction_timestamp AS DATE) = dd.date
        INNER JOIN [dwh].[dim_customer] dc
            ON s.customer_id = dc.customer_id
            AND dc.is_current = 1
        INNER JOIN [dwh].[dim_product] dp
            ON s.product_id = dp.product_id
        INNER JOIN [dwh].[dim_store] ds
            ON s.store_id = ds.store_id
            AND ds.is_current = 1
        LEFT JOIN [dwh].[dim_geography] dg
            ON ds.geography_key = dg.geography_key
            AND dg.is_current = 1
        WHERE 
            s.processing_date = @processing_date
            AND NOT EXISTS (
                -- Avoid duplicates
                SELECT 1 
                FROM [dwh].[fact_sales] f
                WHERE f.transaction_id = s.transaction_id
                    AND f.transaction_timestamp = s.transaction_timestamp
                    AND f.product_key = dp.product_key
            );
        
        COMMIT TRANSACTION;
        
        -- Return summary
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_inserted,
            SUM(net_amount) AS total_sales_amount,
            'Sales Fact Loaded Successfully' AS status
        FROM [dwh].[fact_sales]
        WHERE created_timestamp >= CAST(@processing_date AS DATETIME2);
        
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

