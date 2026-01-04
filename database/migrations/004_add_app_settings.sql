-- Migration: Add app_settings and settings_audit_log tables
-- Version: 1.4
-- Created: 2026-01-04
-- Purpose: Enable editable settings from dashboard - no code editing required

-- ═══════════════════════════════════════════════════════════════════
-- APP SETTINGS TABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS app_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) NOT NULL CHECK(setting_type IN ('string', 'integer', 'decimal', 'boolean', 'json')),
    category VARCHAR(50) NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON app_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_settings_category ON app_settings(category);

-- ═══════════════════════════════════════════════════════════════════
-- SETTINGS AUDIT LOG TABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS settings_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_key ON settings_audit_log(setting_key);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON settings_audit_log(changed_at);

-- ═══════════════════════════════════════════════════════════════════
-- DEFAULT SETTINGS DATA
-- ═══════════════════════════════════════════════════════════════════

-- Payroll Configuration
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('payroll_yahshua_15th', '1000000', 'decimal', 'payroll', 'YAHSHUA payroll amount on 15th'),
    ('payroll_yahshua_30th', '1000000', 'decimal', 'payroll', 'YAHSHUA payroll amount on 30th'),
    ('payroll_abba_15th', '500000', 'decimal', 'payroll', 'ABBA payroll amount on 15th'),
    ('payroll_abba_30th', '500000', 'decimal', 'payroll', 'ABBA payroll amount on 30th');

-- Payment Terms Configuration
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('invoice_lead_days', '15', 'integer', 'payment_terms', 'Days before month to send invoice'),
    ('payment_terms_days', '30', 'integer', 'payment_terms', 'Net payment terms in days'),
    ('realistic_delay_days', '10', 'integer', 'payment_terms', 'Realistic scenario delay days'),
    ('default_reliability', '80', 'integer', 'payment_terms', 'Default reliability percentage');

-- Entity Mapping Configuration
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('entity_mapping', '{"RCBC Partner": "YAHSHUA", "Globe Partner": "YAHSHUA", "YOWI": "YAHSHUA", "TAI": "ABBA", "PEI": "ABBA"}', 'json', 'entity_mapping', 'Acquisition source to entity mapping');

-- Alert Thresholds Configuration
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('alert_cash_warning', '5000000', 'decimal', 'alerts', 'Cash warning threshold (yellow)'),
    ('alert_cash_critical', '2000000', 'decimal', 'alerts', 'Cash critical threshold (red)'),
    ('alert_days_advance', '30', 'integer', 'alerts', 'Days in advance to warn'),
    ('alert_contract_expiry_days', '90', 'integer', 'alerts', 'Days before contract expiry to warn');

-- Google Sheets Configuration
INSERT OR IGNORE INTO app_settings (setting_key, setting_value, setting_type, category, description) VALUES
    ('google_sheets_url', 'https://docs.google.com/spreadsheets/d/1p8p7E6j-EhoYOfCWBCWwYMAzgaALDg9RBADDquVnwTM/edit?gid=0#gid=0', 'string', 'data_source', 'Google Sheets URL'),
    ('sheet_name_customers', 'Customer Contracts', 'string', 'data_source', 'Customer contracts tab name'),
    ('sheet_name_vendors', 'Vendor Contracts', 'string', 'data_source', 'Vendor contracts tab name'),
    ('sheet_name_bank_balances', 'Bank Balances', 'string', 'data_source', 'Bank balances tab name');

-- Update schema version
UPDATE system_metadata SET value = '1.4', updated_at = datetime('now') WHERE key = 'schema_version';

-- ═══════════════════════════════════════════════════════════════════
-- MIGRATION NOTES
-- ═══════════════════════════════════════════════════════════════════
--
-- SETTING TYPES:
--   - string: Plain text value
--   - integer: Whole number
--   - decimal: Currency or percentage values
--   - boolean: 'true' or 'false'
--   - json: JSON-encoded object/array
--
-- CATEGORIES:
--   - payroll: Payroll amounts per entity
--   - payment_terms: Invoice and payment timing
--   - entity_mapping: Acquisition source to entity rules
--   - alerts: Warning thresholds
--   - data_source: Google Sheets configuration
--
-- ═══════════════════════════════════════════════════════════════════
