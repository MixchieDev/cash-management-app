import { mutation } from "./_generated/server";
import { v } from "convex/values";

/**
 * Bulk seed mutation. Call this from the Convex dashboard or a script
 * to import data from the SQLite export.
 *
 * Usage from script:
 *   const data = JSON.parse(fs.readFileSync('scripts/seed-data.json'));
 *   await convex.mutation(api.seed.seedAll, data);
 */
export const seedAll = mutation({
  args: {
    entities: v.array(
      v.object({
        shortCode: v.string(),
        fullName: v.string(),
        isActive: v.boolean(),
        displayOrder: v.number(),
        color: v.optional(v.string()),
      })
    ),
    customerContracts: v.array(
      v.object({
        companyName: v.string(),
        monthlyFee: v.number(),
        paymentPlan: v.string(),
        contractStart: v.string(),
        contractEnd: v.optional(v.string()),
        status: v.string(),
        whoAcquired: v.string(),
        entity: v.string(),
        invoiceDay: v.optional(v.number()),
        paymentTermsDays: v.optional(v.number()),
        reliabilityScore: v.number(),
        notes: v.optional(v.string()),
        source: v.string(),
        createdBy: v.optional(v.string()),
      })
    ),
    vendorContracts: v.array(
      v.object({
        vendorName: v.string(),
        category: v.string(),
        amount: v.number(),
        frequency: v.string(),
        dueDate: v.string(),
        startDate: v.optional(v.string()),
        endDate: v.optional(v.string()),
        entity: v.string(),
        priority: v.number(),
        flexibilityDays: v.number(),
        status: v.string(),
        notes: v.optional(v.string()),
        source: v.string(),
        createdBy: v.optional(v.string()),
      })
    ),
    bankBalances: v.array(
      v.object({
        balanceDate: v.string(),
        entity: v.string(),
        accountName: v.string(),
        balance: v.number(),
        source: v.string(),
        notes: v.optional(v.string()),
      })
    ),
    paymentOverrides: v.array(
      v.object({
        overrideType: v.string(),
        contractId: v.string(),
        originalDate: v.string(),
        newDate: v.optional(v.string()),
        action: v.string(),
        entity: v.string(),
        reason: v.optional(v.string()),
        createdBy: v.optional(v.string()),
      })
    ),
    users: v.array(
      v.object({
        username: v.string(),
        passwordHash: v.string(),
        name: v.string(),
        role: v.string(),
        isActive: v.boolean(),
        permissions: v.array(v.string()),
      })
    ),
    appSettings: v.array(
      v.object({
        settingKey: v.string(),
        settingValue: v.string(),
        settingType: v.string(),
        category: v.string(),
        description: v.optional(v.string()),
        updatedBy: v.optional(v.string()),
      })
    ),
    scenarios: v.array(
      v.object({
        scenarioName: v.string(),
        entity: v.string(),
        description: v.optional(v.string()),
        createdBy: v.optional(v.string()),
        changes: v.array(
          v.object({
            changeType: v.string(),
            startDate: v.string(),
            endDate: v.optional(v.string()),
            employees: v.optional(v.number()),
            salaryPerEmployee: v.optional(v.number()),
            expenseName: v.optional(v.string()),
            expenseAmount: v.optional(v.number()),
            expenseFrequency: v.optional(v.string()),
            newClients: v.optional(v.number()),
            revenuePerClient: v.optional(v.number()),
            investmentAmount: v.optional(v.number()),
            lostRevenue: v.optional(v.number()),
            notes: v.optional(v.string()),
          })
        ),
      })
    ),
  },
  handler: async (ctx, args) => {
    const counts: Record<string, number> = {};

    // Entities
    for (const e of args.entities) {
      await ctx.db.insert("entities", e);
    }
    counts.entities = args.entities.length;

    // Customer Contracts
    for (const c of args.customerContracts) {
      await ctx.db.insert("customerContracts", c);
    }
    counts.customerContracts = args.customerContracts.length;

    // Vendor Contracts
    for (const v of args.vendorContracts) {
      await ctx.db.insert("vendorContracts", v);
    }
    counts.vendorContracts = args.vendorContracts.length;

    // Bank Balances
    for (const b of args.bankBalances) {
      await ctx.db.insert("bankBalances", b);
    }
    counts.bankBalances = args.bankBalances.length;

    // Payment Overrides
    for (const o of args.paymentOverrides) {
      await ctx.db.insert("paymentOverrides", o);
    }
    counts.paymentOverrides = args.paymentOverrides.length;

    // Users
    for (const u of args.users) {
      await ctx.db.insert("users", u);
    }
    counts.users = args.users.length;

    // App Settings
    for (const s of args.appSettings) {
      await ctx.db.insert("appSettings", s);
    }
    counts.appSettings = args.appSettings.length;

    // Scenarios + Changes
    for (const s of args.scenarios) {
      const { changes, ...scenarioData } = s;
      const scenarioId = await ctx.db.insert("scenarios", scenarioData);
      for (const change of changes) {
        await ctx.db.insert("scenarioChanges", { ...change, scenarioId });
      }
    }
    counts.scenarios = args.scenarios.length;

    return counts;
  },
});
