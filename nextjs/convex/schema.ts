import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  // ═══════════════════════════════════════════════════════════════
  // Entities
  // ═══════════════════════════════════════════════════════════════
  entities: defineTable({
    shortCode: v.string(),
    fullName: v.string(),
    isActive: v.boolean(),
    displayOrder: v.number(),
    color: v.optional(v.string()), // hex color, e.g. "#2563eb"
  }).index("by_shortCode", ["shortCode"]),

  // ═══════════════════════════════════════════════════════════════
  // Customer Contracts
  // ═══════════════════════════════════════════════════════════════
  customerContracts: defineTable({
    companyName: v.string(),
    monthlyFee: v.number(), // stored as number, use Decimal in engine
    paymentPlan: v.string(), // Monthly | Quarterly | Annual | Bi-annually | More than 1 year
    contractStart: v.string(), // ISO date string
    contractEnd: v.optional(v.string()),
    status: v.string(), // Active | Inactive | Pending | Cancelled
    whoAcquired: v.string(),
    entity: v.string(), // YAHSHUA | ABBA
    invoiceDay: v.optional(v.number()),
    paymentTermsDays: v.optional(v.number()),
    reliabilityScore: v.number(), // 0-1
    notes: v.optional(v.string()),
    source: v.string(), // manual | google_sheets | csv_import
    createdBy: v.optional(v.string()),
    bankAccount: v.optional(v.string()), // e.g. "RCBC Current" — defaults to "RCBC Current" if unset
  })
    .index("by_entity", ["entity"])
    .index("by_status", ["status"])
    .index("by_entity_status", ["entity", "status"]),

  // ═══════════════════════════════════════════════════════════════
  // Vendor Contracts
  // ═══════════════════════════════════════════════════════════════
  vendorContracts: defineTable({
    vendorName: v.string(),
    category: v.string(), // Payroll | Loans | Software/Tech | Operations | Rent | Utilities
    amount: v.number(),
    frequency: v.string(), // One-time | Daily | Weekly | Bi-weekly | Monthly | Quarterly | Annual
    dueDate: v.string(), // ISO date
    startDate: v.optional(v.string()),
    endDate: v.optional(v.string()),
    entity: v.string(),
    priority: v.number(), // 1-4
    flexibilityDays: v.number(),
    status: v.string(), // Active | Inactive | Paid | Pending
    notes: v.optional(v.string()),
    source: v.string(),
    createdBy: v.optional(v.string()),
    bankAccount: v.optional(v.string()), // e.g. "RCBC Current"
  })
    .index("by_entity", ["entity"])
    .index("by_status", ["status"])
    .index("by_entity_status", ["entity", "status"]),

  // ═══════════════════════════════════════════════════════════════
  // Bank Balances
  // ═══════════════════════════════════════════════════════════════
  bankBalances: defineTable({
    balanceDate: v.string(), // ISO date
    entity: v.string(),
    accountName: v.optional(v.string()), // e.g. "BDO Savings", "RCBC Checking"
    balance: v.number(),
    source: v.string(),
    notes: v.optional(v.string()),
  })
    .index("by_entity", ["entity"])
    .index("by_entity_date", ["entity", "balanceDate"])
    .index("by_entity_account", ["entity", "accountName"]),

  // ═══════════════════════════════════════════════════════════════
  // Scenarios
  // ═══════════════════════════════════════════════════════════════
  scenarios: defineTable({
    scenarioName: v.string(),
    entity: v.string(), // YAHSHUA | ABBA | Consolidated
    description: v.optional(v.string()),
    createdBy: v.optional(v.string()),
  }).index("by_entity", ["entity"]),

  // ═══════════════════════════════════════════════════════════════
  // Scenario Changes
  // ═══════════════════════════════════════════════════════════════
  scenarioChanges: defineTable({
    scenarioId: v.id("scenarios"),
    changeType: v.string(), // hiring | expense | revenue | customer_loss | investment
    startDate: v.string(),
    endDate: v.optional(v.string()),
    // Hiring
    employees: v.optional(v.number()),
    salaryPerEmployee: v.optional(v.number()),
    // Expense
    expenseName: v.optional(v.string()),
    expenseAmount: v.optional(v.number()),
    expenseFrequency: v.optional(v.string()),
    // Revenue
    newClients: v.optional(v.number()),
    revenuePerClient: v.optional(v.number()),
    // Investment
    investmentAmount: v.optional(v.number()),
    // Customer loss
    lostRevenue: v.optional(v.number()),
    notes: v.optional(v.string()),
  }).index("by_scenarioId", ["scenarioId"]),

  // ═══════════════════════════════════════════════════════════════
  // Payment Overrides
  // ═══════════════════════════════════════════════════════════════
  paymentOverrides: defineTable({
    overrideType: v.string(), // customer | vendor
    contractId: v.string(), // Convex ID as string
    originalDate: v.string(),
    newDate: v.optional(v.string()),
    action: v.string(), // move | skip
    entity: v.string(),
    reason: v.optional(v.string()),
    createdBy: v.optional(v.string()),
  })
    .index("by_type", ["overrideType"])
    .index("by_entity", ["entity"]),

  // ═══════════════════════════════════════════════════════════════
  // Users
  // ═══════════════════════════════════════════════════════════════
  users: defineTable({
    username: v.string(),
    passwordHash: v.string(),
    name: v.string(),
    role: v.string(), // admin | editor | viewer
    isActive: v.boolean(),
    permissions: v.array(v.string()), // permission keys stored directly
  }).index("by_username", ["username"]),

  // ═══════════════════════════════════════════════════════════════
  // App Settings
  // ═══════════════════════════════════════════════════════════════
  appSettings: defineTable({
    settingKey: v.string(),
    settingValue: v.string(),
    settingType: v.string(),
    category: v.string(),
    description: v.optional(v.string()),
    updatedBy: v.optional(v.string()),
  }).index("by_key", ["settingKey"]),

  // ═══════════════════════════════════════════════════════════════
  // Settings Audit Log
  // ═══════════════════════════════════════════════════════════════
  settingsAuditLog: defineTable({
    settingKey: v.string(),
    oldValue: v.optional(v.string()),
    newValue: v.string(),
    changedBy: v.optional(v.string()),
  }),
});
