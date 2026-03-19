/**
 * Shared TypeScript types for JESUS Company Cash Management System.
 */

// ═══════════════════════════════════════════════════════════════════
// Entity Types
// ═══════════════════════════════════════════════════════════════════
export type EntityCode = 'YAHSHUA' | 'ABBA';
export type EntityOrConsolidated = EntityCode | 'Consolidated';

// ═══════════════════════════════════════════════════════════════════
// Contract Types
// ═══════════════════════════════════════════════════════════════════
export type PaymentPlan = 'Monthly' | 'Quarterly' | 'Annual' | 'Bi-annually' | 'More than 1 year';
export type ContractStatus = 'Active' | 'Inactive' | 'Pending' | 'Cancelled';
export type ExpenseFrequency = 'One-time' | 'Daily' | 'Weekly' | 'Bi-weekly' | 'Monthly' | 'Quarterly' | 'Annual';
export type ExpenseCategory = 'Payroll' | 'Loans' | 'Software/Tech' | 'Operations' | 'Rent' | 'Utilities';
export type VendorStatus = 'Active' | 'Inactive' | 'Paid' | 'Pending';

// ═══════════════════════════════════════════════════════════════════
// Projection Types
// ═══════════════════════════════════════════════════════════════════
export type Timeframe = 'daily' | 'weekly' | 'monthly' | 'quarterly';
export type ScenarioType = 'optimistic' | 'realistic';

// ═══════════════════════════════════════════════════════════════════
// Scenario Types
// ═══════════════════════════════════════════════════════════════════
export type ChangeType = 'hiring' | 'expense' | 'revenue' | 'customer_loss' | 'investment';

// ═══════════════════════════════════════════════════════════════════
// Override Types
// ═══════════════════════════════════════════════════════════════════
export type OverrideType = 'customer' | 'vendor';
export type OverrideAction = 'move' | 'skip';

// ═══════════════════════════════════════════════════════════════════
// Auth Types
// ═══════════════════════════════════════════════════════════════════
export type UserRole = 'admin' | 'editor' | 'viewer';

export type PermissionKey =
  | 'view_dashboard'
  | 'view_contracts'
  | 'edit_contracts'
  | 'view_scenarios'
  | 'edit_scenarios'
  | 'manage_overrides'
  | 'import_data'
  | 'manage_settings'
  | 'delete_data'
  | 'manage_users';

// ═══════════════════════════════════════════════════════════════════
// Settings Types
// ═══════════════════════════════════════════════════════════════════
export type SettingType = 'string' | 'integer' | 'decimal' | 'boolean' | 'json';

// ═══════════════════════════════════════════════════════════════════
// Data Interfaces (Convex document shapes)
// ═══════════════════════════════════════════════════════════════════
export interface CustomerContract {
  _id: string;
  _creationTime: number;
  companyName: string;
  monthlyFee: number;
  paymentPlan: PaymentPlan;
  contractStart: string; // ISO date string
  contractEnd?: string;
  status: ContractStatus;
  whoAcquired: string;
  entity: EntityCode;
  invoiceDay?: number;
  paymentTermsDays?: number;
  reliabilityScore: number;
  notes?: string;
  source: string;
  createdBy?: string;
}

export interface VendorContract {
  _id: string;
  _creationTime: number;
  vendorName: string;
  category: ExpenseCategory;
  amount: number;
  frequency: ExpenseFrequency;
  dueDate: string;
  startDate?: string;
  endDate?: string;
  entity: EntityCode;
  priority: number;
  flexibilityDays: number;
  status: VendorStatus;
  notes?: string;
  source: string;
  createdBy?: string;
}

export interface BankBalance {
  _id: string;
  _creationTime: number;
  balanceDate: string;
  entity: EntityCode;
  balance: number;
  source: string;
  notes?: string;
}

export interface ProjectionDataPoint {
  date: string;
  startingCash: string;
  inflows: string;
  outflows: string;
  endingCash: string;
  entity: string;
  timeframe: Timeframe;
  scenarioType: ScenarioType;
  isNegative: boolean;
}

export interface RevenueEvent {
  date: string;
  customerId: string;
  companyName: string;
  amount: string;
  entity: string;
  eventType: string;
  paymentPlan: string;
}

export interface ExpenseEvent {
  date: string;
  vendorId: string | null;
  vendorName: string;
  amount: string;
  entity: string;
  category: string;
  priority: number;
  isPayroll: boolean;
}

export interface ProjectionResult {
  dataPoints: ProjectionDataPoint[];
  revenueEvents: RevenueEvent[];
  expenseEvents: ExpenseEvent[];
}

export interface PaymentOverride {
  _id: string;
  _creationTime: number;
  overrideType: OverrideType;
  contractId: string;
  originalDate: string;
  newDate?: string;
  action: OverrideAction;
  entity: EntityCode;
  reason?: string;
  createdBy?: string;
}
