-- Migration: Add start_date column to vendor_contracts
-- Version: 1.1
-- Created: 2026-01-03
-- Purpose: Support vendor expenses that become active on a specific date

-- ═══════════════════════════════════════════════════════════════════
-- ADD START_DATE COLUMN TO VENDOR_CONTRACTS
-- ═══════════════════════════════════════════════════════════════════

-- Add start_date column (nullable, default NULL)
-- If start_date is NULL or in the past, vendor expense is already active
-- If start_date is in the future, vendor expense only appears in projections from that date onwards
ALTER TABLE vendor_contracts ADD COLUMN start_date DATE;

-- Create index for efficient queries on start_date
CREATE INDEX IF NOT EXISTS idx_vendor_start_date ON vendor_contracts(start_date);

-- Update schema version in metadata
UPDATE system_metadata SET value = '1.1', updated_at = datetime('now') WHERE key = 'schema_version';

-- ═══════════════════════════════════════════════════════════════════
-- MIGRATION NOTES
-- ═══════════════════════════════════════════════════════════════════
--
-- EXISTING VENDORS:
--   - All existing vendor contracts will have start_date = NULL
--   - NULL means vendor is already active (treat as if started in the past)
--
-- NEW VENDORS:
--   - Can specify start_date when importing from Google Sheets
--   - If start_date is empty in Google Sheets, it will be NULL (active)
--   - If start_date is in the future, expense only appears from that date
--
-- PROJECTION ENGINE:
--   - Must check if vendor.start_date <= projection_date before including expense
--   - If start_date is NULL, include expense (already active)
--
-- ═══════════════════════════════════════════════════════════════════
