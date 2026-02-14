-- Stored Procedure: Load Inventory Fact Table (Snapshot)

CREATE OR ALTER PROCEDURE [dwh].[sp_load_inventory_fact]
    @processing_date DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    IF @processing_date IS NULL
        SET @processing_date = CAST(GETDATE() AS DATE);
    
    BEGIN TRANSACTION;
    
    BEGIN TRY
        -- Delete existing snapshot for this date (if exists)
        DELETE FROM [dwh].[fact_inventory]
        WHERE snapshot_date = @processing_date;
        
        -- Insert new snapshot
        INSERT INTO [dwh].[fact_inventory] (
            [date_key],
            [product_key],
            [store_key],
            [snapshot_date],
            [quantity_on_hand],
            [quantity_reserved],
            [quantity_available],
            [reorder_level],
            [reorder_quantity],
            [unit_cost],
            [total_value],
            [created_timestamp]
        )
        SELECT 
            dd.date_key,
            dp.product_key,
            ds.store_key,
            @processing_date AS snapshot_date,
            COALESCE(i.quantity_on_hand, 0) AS quantity_on_hand,
            COALESCE(i.quantity_reserved, 0) AS quantity_reserved,
            COALESCE(i.quantity_on_hand, 0) - COALESCE(i.quantity_reserved, 0) AS quantity_available,
            i.reorder_level,
            i.reorder_quantity,
            i.unit_cost,
            COALESCE(i.quantity_on_hand, 0) * COALESCE(i.unit_cost, 0) AS total_value,
            GETDATE() AS created_timestamp
        FROM [staging].[inventory] i  -- Assuming inventory staging table exists
        INNER JOIN [dwh].[dim_date] dd
            ON @processing_date = dd.date
        INNER JOIN [dwh].[dim_product] dp
            ON i.product_id = dp.product_id
        INNER JOIN [dwh].[dim_store] ds
            ON i.store_id = ds.store_id
            AND ds.is_current = 1
        WHERE i.processing_date = @processing_date;
        
        COMMIT TRANSACTION;
        
        SELECT 
            @processing_date AS processing_date,
            COUNT(*) AS records_inserted,
            'Inventory Fact Loaded Successfully' AS status
        FROM [dwh].[fact_inventory]
        WHERE snapshot_date = @processing_date;
        
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

