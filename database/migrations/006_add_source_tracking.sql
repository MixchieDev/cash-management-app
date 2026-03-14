-- Migration 006: Add source tracking columns to customer and vendor contracts
-- Tracks whether records were created manually in-app or imported from Google Sheets

ALTER TABLE customer_contracts ADD COLUMN source VARCHAR DEFAULT 'manual';
ALTER TABLE customer_contracts ADD COLUMN created_by VARCHAR;

ALTER TABLE vendor_contracts ADD COLUMN source VARCHAR DEFAULT 'manual';
ALTER TABLE vendor_contracts ADD COLUMN created_by VARCHAR;
