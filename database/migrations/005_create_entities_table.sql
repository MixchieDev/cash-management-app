-- Migration: Create entities table for dynamic legal entity management
-- Version: 1.5
-- Created: 2026-01-04
-- Purpose: Allow CFO to add/edit legal entities from dashboard

-- ═══════════════════════════════════════════════════════════════════
-- ENTITIES TABLE
-- ═══════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_entities_active ON entities(is_active);
CREATE INDEX IF NOT EXISTS idx_entities_order ON entities(display_order);

-- ═══════════════════════════════════════════════════════════════════
-- SEED DEFAULT ENTITIES
-- ═══════════════════════════════════════════════════════════════════

INSERT OR IGNORE INTO entities (short_code, full_name, display_order) VALUES
    ('YAHSHUA', 'YAHSHUA Outsourcing Worldwide Inc', 1),
    ('ABBA', 'The ABBA Initiative OPC', 2);

-- Update schema version
UPDATE system_metadata SET value = '1.5', updated_at = datetime('now') WHERE key = 'schema_version';

-- ═══════════════════════════════════════════════════════════════════
-- MIGRATION NOTES
-- ═══════════════════════════════════════════════════════════════════
--
-- ENTITY FIELDS:
--   - short_code: Unique identifier (e.g., "YAHSHUA", "ABBA")
--   - full_name: Full legal name (e.g., "YAHSHUA Outsourcing Worldwide Inc")
--   - is_active: Whether entity is active (inactive entities hidden from UI)
--   - display_order: Order for display in UI (lower = first)
--
-- USAGE:
--   - New entities can be added from Settings > Entities tab
--   - Consolidated projections automatically include ALL active entities
--   - Entity mappings use these entities as targets
--
-- ═══════════════════════════════════════════════════════════════════
