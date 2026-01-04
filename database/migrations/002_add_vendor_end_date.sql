-- Migration: Add end_date column to vendor_contracts
-- Purpose: Allow vendor expenses to have an end date
-- If end_date is NULL, vendor expense continues indefinitely (current behavior)
-- If end_date is specified, vendor expense stops after that date

-- Check if column exists before adding (SQLite doesn't support IF NOT EXISTS for columns)
-- This migration is idempotent - safe to run multiple times

-- Add end_date column (nullable, default NULL)
-- If end_date is NULL, vendor expense continues indefinitely
-- If end_date is specified, vendor expense only appears in projections up to that date
ALTER TABLE vendor_contracts ADD COLUMN end_date DATE;

-- Create index for efficient queries on end_date
CREATE INDEX IF NOT EXISTS idx_vendor_end_date ON vendor_contracts(end_date);

-- ═══════════════════════════════════════════════════════════════════════════
-- Usage Examples:
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Vendor with no end date (continues indefinitely - current behavior):
--    INSERT INTO vendor_contracts (vendor_name, ..., end_date) VALUES ('AWS', ..., NULL);
--
-- 2. Vendor with specific end date:
--    INSERT INTO vendor_contracts (vendor_name, ..., end_date) VALUES ('Contractor', ..., '2026-06-30');
--
-- 3. Update existing vendor to add end date:
--    UPDATE vendor_contracts SET end_date = '2026-12-31' WHERE vendor_name = 'Contractor';
--
-- ═══════════════════════════════════════════════════════════════════════════
-- Impact:
-- ═══════════════════════════════════════════════════════════════════════════
--
-- - All existing vendor contracts will have end_date = NULL (continues indefinitely)
-- - expense_scheduler.py will filter out payments after end_date
-- - Can specify end_date when importing from Google Sheets
-- - If end_date is empty in Google Sheets, it will be NULL (continues indefinitely)
