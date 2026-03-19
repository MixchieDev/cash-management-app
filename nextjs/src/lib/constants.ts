/**
 * Business constants for JESUS Company Cash Management System.
 * Port of config/constants.py
 */

// ═══════════════════════════════════════════════════════════════════
// PAYMENT PLANS
// ═══════════════════════════════════════════════════════════════════
export const PAYMENT_PLAN_FREQUENCIES: Record<string, number> = {
  'Monthly': 1,
  'Quarterly': 3,
  'Bi-annually': 6,
  'Annual': 12,
  'More than 1 year': 12,
};

export const VALID_PAYMENT_PLANS = Object.keys(PAYMENT_PLAN_FREQUENCIES);

// ═══════════════════════════════════════════════════════════════════
// VENDOR EXPENSE FREQUENCIES
// ═══════════════════════════════════════════════════════════════════
export const EXPENSE_FREQUENCIES: Record<string, number | null> = {
  'One-time': null,
  'Daily': 1,
  'Weekly': 7,
  'Bi-weekly': 14,
  'Monthly': 30,
  'Quarterly': 90,
  'Annual': 365,
};

export const VALID_EXPENSE_FREQUENCIES = Object.keys(EXPENSE_FREQUENCIES);

// ═══════════════════════════════════════════════════════════════════
// EXPENSE CATEGORIES
// ═══════════════════════════════════════════════════════════════════
export const EXPENSE_CATEGORIES: Record<string, { priority: number; flexibilityDays: number; description: string }> = {
  'Payroll': { priority: 1, flexibilityDays: 0, description: 'Employee salaries and benefits' },
  'Loans': { priority: 2, flexibilityDays: 2, description: 'Loan amortization and interest' },
  'Software/Tech': { priority: 3, flexibilityDays: 7, description: 'SaaS, AWS, Google Workspace, etc.' },
  'Operations': { priority: 4, flexibilityDays: 14, description: 'Rent, utilities, supplies, meals, fuel' },
  'Rent': { priority: 4, flexibilityDays: 5, description: 'Office rent' },
  'Utilities': { priority: 4, flexibilityDays: 10, description: 'Electricity, water, internet' },
};

export const VALID_EXPENSE_CATEGORIES = Object.keys(EXPENSE_CATEGORIES);

// ═══════════════════════════════════════════════════════════════════
// CONTRACT STATUSES
// ═══════════════════════════════════════════════════════════════════
export const VALID_CONTRACT_STATUSES = ['Active', 'Inactive', 'Pending', 'Cancelled'] as const;

// ═══════════════════════════════════════════════════════════════════
// SCENARIO CHANGE TYPES
// ═══════════════════════════════════════════════════════════════════
export const VALID_SCENARIO_CHANGE_TYPES = ['hiring', 'expense', 'revenue', 'customer_loss', 'investment'] as const;

// ═══════════════════════════════════════════════════════════════════
// PROJECTION TIMEFRAMES & SCENARIO TYPES
// ═══════════════════════════════════════════════════════════════════
export const VALID_TIMEFRAMES = ['daily', 'weekly', 'monthly', 'quarterly'] as const;
export const VALID_SCENARIO_TYPES = ['optimistic', 'realistic'] as const;

// ═══════════════════════════════════════════════════════════════════
// PROJECTION DEFAULTS
// ═══════════════════════════════════════════════════════════════════
export const DEFAULT_PROJECTION_MONTHS = 12;
export const MAX_PROJECTION_MONTHS = 36;

// ═══════════════════════════════════════════════════════════════════
// PAYMENT TERMS DEFAULTS
// ═══════════════════════════════════════════════════════════════════
export const DEFAULT_PAYMENT_TERMS = {
  invoiceLeadDays: 15,
  paymentTermsDays: 30,
  realisticDelayDays: 10,
  defaultReliability: 80,
};
