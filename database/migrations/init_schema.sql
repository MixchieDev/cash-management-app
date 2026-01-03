-- JESUS Company Strategic Cash Management System
-- Database Schema - Version 1.0
-- Created: 2026-01-03

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ═══════════════════════════════════════════════════════════════════
-- CUSTOMER CONTRACTS
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS customer_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    monthly_fee DECIMAL(15, 2) NOT NULL,
    payment_plan TEXT NOT NULL CHECK(payment_plan IN ('Monthly', 'Quarterly', 'Annual', 'Bi-annually', 'More than 1 year')),
    contract_start DATE NOT NULL,
    contract_end DATE,
    status TEXT NOT NULL CHECK(status IN ('Active', 'Inactive', 'Pending', 'Cancelled')),
    who_acquired TEXT NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('YAHSHUA', 'ABBA')),
    invoice_day INTEGER DEFAULT 15 CHECK(invoice_day BETWEEN 1 AND 28),
    payment_terms_days INTEGER DEFAULT 30,
    reliability_score DECIMAL(3, 2) DEFAULT 0.80 CHECK(reliability_score BETWEEN 0 AND 1),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customer_entity ON customer_contracts(entity);
CREATE INDEX idx_customer_status ON customer_contracts(status);
CREATE INDEX idx_customer_start_date ON customer_contracts(contract_start);

-- ═══════════════════════════════════════════════════════════════════
-- VENDOR CONTRACTS
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS vendor_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('Payroll', 'Loans', 'Software/Tech', 'Operations', 'Rent', 'Utilities')),
    amount DECIMAL(15, 2) NOT NULL,
    frequency TEXT NOT NULL CHECK(frequency IN ('One-time', 'Daily', 'Weekly', 'Bi-weekly', 'Monthly', 'Quarterly', 'Annual')),
    due_date DATE NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('YAHSHUA', 'ABBA', 'Both')),
    priority INTEGER DEFAULT 3 CHECK(priority BETWEEN 1 AND 4),
    flexibility_days INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Paid', 'Pending')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendor_entity ON vendor_contracts(entity);
CREATE INDEX idx_vendor_category ON vendor_contracts(category);
CREATE INDEX idx_vendor_due_date ON vendor_contracts(due_date);

-- ═══════════════════════════════════════════════════════════════════
-- BANK BALANCES (Source of Truth for Starting Cash)
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS bank_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    balance_date DATE NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('YAHSHUA', 'ABBA')),
    balance DECIMAL(15, 2) NOT NULL,
    source TEXT DEFAULT 'Manual Entry',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(balance_date, entity)
);

CREATE INDEX idx_bank_balance_date ON bank_balances(balance_date DESC);
CREATE INDEX idx_bank_entity ON bank_balances(entity);

-- ═══════════════════════════════════════════════════════════════════
-- SCENARIOS (What-If Analysis)
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_name TEXT NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('YAHSHUA', 'ABBA', 'Consolidated')),
    description TEXT,
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════════
-- SCENARIO CHANGES (Modifications to Baseline)
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS scenario_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id INTEGER NOT NULL,
    change_type TEXT NOT NULL CHECK(change_type IN ('hiring', 'expense', 'revenue', 'customer_loss', 'investment')),
    start_date DATE NOT NULL,
    end_date DATE,
    -- Hiring fields
    employees INTEGER,
    salary_per_employee DECIMAL(15, 2),
    -- Expense fields
    expense_name TEXT,
    expense_amount DECIMAL(15, 2),
    expense_frequency TEXT,
    -- Revenue fields
    new_clients INTEGER,
    revenue_per_client DECIMAL(15, 2),
    -- Investment fields
    investment_amount DECIMAL(15, 2),
    -- Customer loss fields
    lost_revenue DECIMAL(15, 2),
    notes TEXT,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE INDEX idx_scenario_changes_scenario ON scenario_changes(scenario_id);

-- ═══════════════════════════════════════════════════════════════════
-- PROJECTIONS (Cached Projection Results)
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS projections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    projection_date DATE NOT NULL,
    entity TEXT NOT NULL CHECK(entity IN ('YAHSHUA', 'ABBA', 'Consolidated')),
    timeframe TEXT NOT NULL CHECK(timeframe IN ('daily', 'weekly', 'monthly', 'quarterly')),
    scenario_type TEXT NOT NULL CHECK(scenario_type IN ('optimistic', 'realistic')),
    scenario_id INTEGER,
    starting_cash DECIMAL(15, 2) NOT NULL,
    inflows DECIMAL(15, 2) NOT NULL DEFAULT 0,
    outflows DECIMAL(15, 2) NOT NULL DEFAULT 0,
    ending_cash DECIMAL(15, 2) NOT NULL,
    is_negative BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE SET NULL
);

CREATE INDEX idx_projection_date ON projections(projection_date);
CREATE INDEX idx_projection_entity ON projections(entity);
CREATE INDEX idx_projection_scenario ON projections(scenario_id);

-- ═══════════════════════════════════════════════════════════════════
-- SYSTEM METADATA
-- ═══════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial metadata
INSERT OR REPLACE INTO system_metadata (key, value) VALUES
    ('schema_version', '1.0'),
    ('last_google_sheets_sync', ''),
    ('created_at', datetime('now'));
