-- Load Inventory Fact Table
-- Loads daily inventory snapshots

INSERT INTO `{project_id}.{curated_dataset}.inventory_fact`
(
    product_id,
    store_id,
    snapshot_date,
    quantity_on_hand,
    quantity_reserved,
    quantity_available,
    reorder_level,
    needs_reorder,
    load_timestamp
)
SELECT 
    inv.product_id,
    inv.store_id,
    inv.snapshot_date,
    inv.quantity_on_hand,
    inv.quantity_reserved,
    inv.quantity_on_hand - inv.quantity_reserved AS quantity_available,
    inv.reorder_level,
    CASE 
        WHEN (inv.quantity_on_hand - inv.quantity_reserved) <= inv.reorder_level 
        THEN TRUE 
        ELSE FALSE 
    END AS needs_reorder,
    CURRENT_TIMESTAMP() AS load_timestamp
FROM `{project_id}.{staging_dataset}.inventory_staging` inv
WHERE inv.snapshot_date = DATE('{load_date}')
AND (inv.product_id, inv.store_id, inv.snapshot_date) NOT IN (
    -- Avoid duplicates
    SELECT product_id, store_id, snapshot_date
    FROM `{project_id}.{curated_dataset}.inventory_fact`
    WHERE snapshot_date = DATE('{load_date}')
);

