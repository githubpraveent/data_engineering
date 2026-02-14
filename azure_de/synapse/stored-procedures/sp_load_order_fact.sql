-- Stored Procedure: Load Order Fact Table

CREATE OR ALTER PROCEDURE [dwh].[sp_load_order_fact]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        INSERT INTO [dwh].[fact_orders] (
            [date_key],
            [customer_key],
            [store_key],
            [geography_key],
            [order_id],
            [order_date],
            [order_status],
            [total_amount],
            [shipping_cost],
            [tax_amount],
            [discount_amount],
            [net_amount],
            [item_count],
            [created_timestamp]
        )
        SELECT 
            dd.date_key,
            dc.customer_key,
            ds.store_key,
            dg.geography_key,
            s.order_id,
            s.order_date,
            s.order_status,
            s.total_amount,
            COALESCE(s.shipping_cost, 0) AS shipping_cost,
            COALESCE(s.tax_amount, 0) AS tax_amount,
            COALESCE(s.discount_amount, 0) AS discount_amount,
            s.total_amount - COALESCE(s.discount_amount, 0) + COALESCE(s.tax_amount, 0) AS net_amount,
            1 AS item_count,  -- Placeholder, adjust based on actual source
            GETDATE() AS created_timestamp
        FROM [staging].[orders] s
        INNER JOIN [dwh].[dim_date] dd
            ON CAST(s.order_date AS DATE) = dd.date
        INNER JOIN [dwh].[dim_customer] dc
            ON s.customer_id = dc.customer_id
            AND dc.is_current = 1
        INNER JOIN [dwh].[dim_store] ds
            ON s.store_id = ds.store_id
            AND ds.is_current = 1
        LEFT JOIN [dwh].[dim_geography] dg
            ON ds.geography_key = dg.geography_key
            AND dg.is_current = 1
        WHERE 
            s.processing_date = @processing_date
            AND NOT EXISTS (
                SELECT 1 
                FROM [dwh].[fact_orders] f
                WHERE f.order_id = s.order_id
            );
        
        COMMIT TRANSACTION;
        
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_inserted,
            SUM(net_amount) AS total_order_amount,
            'Order Fact Loaded Successfully' AS status
        FROM [dwh].[fact_orders]
        WHERE created_timestamp >= CAST(@processing_date AS DATETIME2);
        
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

