-- Migration: Add payment_overrides table
-- Purpose: Allow one-off payment date overrides for customer and vendor payments
-- Overrides can either move a payment to a new date or skip it entirely

-- Create payment_overrides table
CREATE TABLE IF NOT EXISTS payment_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Type: 'customer' or 'vendor'
    override_type VARCHAR NOT NULL CHECK (override_type IN ('customer', 'vendor')),

    -- Reference to the contract (customer_contract_id or vendor_contract_id)
    contract_id INTEGER NOT NULL,

    -- The original scheduled date being overridden
    original_date DATE NOT NULL,

    -- The new payment date (NULL = skip payment entirely)
    new_date DATE,

    -- Action: 'move' or 'skip'
    action VARCHAR NOT NULL DEFAULT 'move' CHECK (action IN ('move', 'skip')),

    -- Entity for filtering
    entity VARCHAR NOT NULL CHECK (entity IN ('YAHSHUA', 'ABBA')),

    -- Optional reason/notes
    reason TEXT,

    -- Audit fields
    created_by VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Unique constraint: only one override per contract + original date + type
CREATE UNIQUE INDEX IF NOT EXISTS uq_override_contract_date
    ON payment_overrides(override_type, contract_id, original_date);

-- Index for efficient lookups by entity and date range
CREATE INDEX IF NOT EXISTS idx_override_entity_date
    ON payment_overrides(entity, original_date);

-- Index for efficient lookups by override_type
CREATE INDEX IF NOT EXISTS idx_override_type
    ON payment_overrides(override_type);

-- ═══════════════════════════════════════════════════════════════════════════
-- Usage Examples:
-- ═══════════════════════════════════════════════════════════════════════════
--
-- 1. Move a customer payment from Jan 15 to Jan 25:
--    INSERT INTO payment_overrides (override_type, contract_id, original_date, new_date, action, entity, reason)
--    VALUES ('customer', 1, '2026-01-15', '2026-01-25', 'move', 'YAHSHUA', 'Client requested delay');
--
-- 2. Skip a vendor payment entirely:
--    INSERT INTO payment_overrides (override_type, contract_id, original_date, new_date, action, entity, reason)
--    VALUES ('vendor', 5, '2026-02-21', NULL, 'skip', 'YAHSHUA', 'Billing dispute');
--
-- 3. Get all overrides for a projection period:
--    SELECT * FROM payment_overrides
--    WHERE original_date BETWEEN '2026-01-01' AND '2026-03-31'
--    AND entity = 'YAHSHUA';
--
-- ═══════════════════════════════════════════════════════════════════════════
