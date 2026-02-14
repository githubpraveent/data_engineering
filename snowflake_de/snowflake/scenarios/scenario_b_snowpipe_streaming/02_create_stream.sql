-- ============================================================================
-- Scenario B: Real-Time Ingestion - Create Stream on POS Events
-- Stream captures changes for downstream processing
-- ============================================================================

USE DATABASE DEV_STAGING;
USE SCHEMA STREAMS;

-- ============================================================================
-- Stream: POS Events Changes
-- ============================================================================

CREATE OR REPLACE STREAM stream_pos_events_changes
ON TABLE DEV_RAW.BRONZE.pos_events
COMMENT = 'Stream to capture changes in POS events table for CDC processing';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT SELECT ON STREAM DEV_STAGING.STREAMS.stream_pos_events_changes TO ROLE DATA_ENGINEER;

-- ============================================================================
-- View Stream Status
-- ============================================================================

-- Check if stream has data
-- SELECT SYSTEM$STREAM_HAS_DATA('DEV_STAGING.STREAMS.stream_pos_events_changes');

-- View stream contents
-- SELECT * FROM DEV_STAGING.STREAMS.stream_pos_events_changes LIMIT 10;

