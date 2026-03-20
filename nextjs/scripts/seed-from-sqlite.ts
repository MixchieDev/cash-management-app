/**
 * Seed Convex database from existing SQLite database.
 *
 * Prerequisites:
 *   1. Run `npx convex dev` to create your Convex project and generate types
 *   2. Install: npm install better-sqlite3 tsx && npm install -D @types/better-sqlite3
 *
 * Usage:
 *   npx tsx scripts/seed-from-sqlite.ts
 */
import Database from "better-sqlite3";
import { ConvexHttpClient } from "convex/browser";
import { api } from "../convex/_generated/api";
import * as fs from "fs";
import * as dotenv from "dotenv";

dotenv.config({ path: ".env.local" });

const SQLITE_PATH = "../database/jesus_cash_management.db";
const CONVEX_URL = process.env.NEXT_PUBLIC_CONVEX_URL;

if (!CONVEX_URL || CONVEX_URL.includes("placeholder")) {
  console.error("❌ Set NEXT_PUBLIC_CONVEX_URL in .env.local to your real Convex URL first.");
  console.error("   Run `npx convex dev` to create a project.");
  process.exit(1);
}

const sqlite = new Database(SQLITE_PATH, { readonly: true });
const convex = new ConvexHttpClient(CONVEX_URL);

function readTable(table: string): any[] {
  return sqlite.prepare(`SELECT * FROM ${table}`).all();
}

async function seed() {
  console.log("🌱 Seeding Convex from SQLite...\n");
  console.log(`   SQLite: ${SQLITE_PATH}`);
  console.log(`   Convex: ${CONVEX_URL}\n`);

  // Build seed data
  const entities = readTable("entities").map((e: any) => ({
    shortCode: e.short_code,
    fullName: e.full_name,
    isActive: Boolean(e.is_active),
    displayOrder: e.display_order ?? 0,
  }));

  const customerContracts = readTable("customer_contracts").map((c: any) => ({
    companyName: c.company_name,
    monthlyFee: parseFloat(c.monthly_fee) || 0,
    paymentPlan: c.payment_plan,
    contractStart: c.contract_start,
    ...(c.contract_end ? { contractEnd: c.contract_end } : {}),
    status: c.status,
    whoAcquired: c.who_acquired,
    entity: c.entity,
    ...(c.invoice_day ? { invoiceDay: c.invoice_day } : {}),
    ...(c.payment_terms_days ? { paymentTermsDays: c.payment_terms_days } : {}),
    reliabilityScore: parseFloat(c.reliability_score) || 0.8,
    ...(c.notes ? { notes: c.notes } : {}),
    source: c.source || "sqlite_import",
    ...(c.created_by ? { createdBy: c.created_by } : {}),
  }));

  const vendorContracts = readTable("vendor_contracts").map((v: any) => ({
    vendorName: v.vendor_name,
    category: v.category,
    amount: parseFloat(v.amount) || 0,
    frequency: v.frequency,
    dueDate: v.due_date,
    ...(v.start_date ? { startDate: v.start_date } : {}),
    ...(v.end_date ? { endDate: v.end_date } : {}),
    entity: v.entity,
    priority: v.priority ?? 3,
    flexibilityDays: v.flexibility_days ?? 0,
    status: v.status || "Active",
    ...(v.notes ? { notes: v.notes } : {}),
    source: v.source || "sqlite_import",
    ...(v.created_by ? { createdBy: v.created_by } : {}),
  }));

  const bankBalances = readTable("bank_balances").map((b: any) => ({
    balanceDate: b.balance_date,
    entity: b.entity,
    accountName: b.account_name || "Main Account",
    balance: parseFloat(b.balance) || 0,
    source: b.source || "sqlite_import",
    ...(b.notes ? { notes: b.notes } : {}),
  }));

  const overrides = readTable("payment_overrides").map((o: any) => ({
    overrideType: o.override_type,
    contractId: String(o.contract_id),
    originalDate: o.original_date,
    ...(o.new_date ? { newDate: o.new_date } : {}),
    action: o.action,
    entity: o.entity,
    ...(o.reason ? { reason: o.reason } : {}),
    ...(o.created_by ? { createdBy: o.created_by } : {}),
  }));

  const rawUsers = readTable("users");
  const rawPerms = readTable("user_permissions").filter((p: any) => p.granted);
  const users = rawUsers.map((u: any) => ({
    username: u.username,
    passwordHash: u.password_hash,
    name: u.name,
    role: u.role || "viewer",
    isActive: Boolean(u.is_active),
    permissions: rawPerms
      .filter((p: any) => p.user_id === u.id)
      .map((p: any) => p.permission),
  }));

  const rawSettings = readTable("app_settings");
  const appSettings = rawSettings.map((s: any) => ({
    settingKey: s.setting_key,
    settingValue: s.setting_value,
    settingType: s.setting_type || "string",
    category: s.category || "general",
    ...(s.description ? { description: s.description } : {}),
    ...(s.updated_by ? { updatedBy: s.updated_by } : {}),
  }));

  const rawScenarios = readTable("scenarios");
  const rawChanges = readTable("scenario_changes");
  const scenarios = rawScenarios.map((s: any) => ({
    scenarioName: s.scenario_name,
    entity: s.entity,
    ...(s.description ? { description: s.description } : {}),
    ...(s.created_by ? { createdBy: s.created_by } : {}),
    changes: rawChanges
      .filter((c: any) => c.scenario_id === s.id)
      .map((c: any) => ({
        changeType: c.change_type,
        startDate: c.start_date,
        ...(c.end_date ? { endDate: c.end_date } : {}),
        ...(c.employees ? { employees: c.employees } : {}),
        ...(c.salary_per_employee ? { salaryPerEmployee: parseFloat(c.salary_per_employee) } : {}),
        ...(c.expense_name ? { expenseName: c.expense_name } : {}),
        ...(c.expense_amount ? { expenseAmount: parseFloat(c.expense_amount) } : {}),
        ...(c.expense_frequency ? { expenseFrequency: c.expense_frequency } : {}),
        ...(c.new_clients ? { newClients: c.new_clients } : {}),
        ...(c.revenue_per_client ? { revenuePerClient: parseFloat(c.revenue_per_client) } : {}),
        ...(c.investment_amount ? { investmentAmount: parseFloat(c.investment_amount) } : {}),
        ...(c.lost_revenue ? { lostRevenue: parseFloat(c.lost_revenue) } : {}),
        ...(c.notes ? { notes: c.notes } : {}),
      })),
  }));

  const seedData = {
    entities,
    customerContracts,
    vendorContracts,
    bankBalances,
    paymentOverrides: overrides,
    users,
    appSettings,
    scenarios,
  };

  // Write JSON backup
  fs.writeFileSync("scripts/seed-data.json", JSON.stringify(seedData, null, 2));
  console.log("📝 Seed data saved to scripts/seed-data.json\n");

  // Print summary
  console.log("📊 Data summary:");
  console.log(`   Entities:           ${entities.length}`);
  console.log(`   Customer Contracts: ${customerContracts.length}`);
  console.log(`   Vendor Contracts:   ${vendorContracts.length}`);
  console.log(`   Bank Balances:      ${bankBalances.length}`);
  console.log(`   Payment Overrides:  ${overrides.length}`);
  console.log(`   Users:              ${users.length}`);
  console.log(`   App Settings:       ${appSettings.length}`);
  console.log(`   Scenarios:          ${scenarios.length}`);
  console.log(`   Total:              ${Object.values(seedData).reduce((s, a) => s + a.length, 0)}\n`);

  // Call Convex seed mutation
  console.log("🚀 Sending to Convex...");
  try {
    const result = await convex.mutation(api.seed.seedAll as any, seedData);
    console.log("✅ Seed complete!", result);
  } catch (error: any) {
    console.log(`⚠️  Bulk seed failed: ${error.message}\n   Falling back to batch mode...\n`);
    await seedInBatches(seedData);
  }

  sqlite.close();
}

async function seedInBatches(data: any) {
  // Seed each table separately
  for (const [table, records] of Object.entries(data) as [string, any[]][]) {
    if (table === "scenarios") {
      // Scenarios need special handling (nested changes)
      for (const s of records) {
        try {
          await convex.mutation(api.scenarios.create as any, s);
        } catch (e: any) {
          console.error(`  ⚠️  Failed to seed scenario "${s.scenarioName}": ${e.message}`);
        }
      }
      console.log(`  ✅ scenarios: ${records.length}`);
      continue;
    }

    const mutationMap: Record<string, any> = {
      entities: null, // No direct mutation, use seedAll for just entities
      customerContracts: api.customers.create,
      vendorContracts: api.vendors.create,
      bankBalances: api.bankBalances.create,
      paymentOverrides: api.overrides.create,
      users: api.users.create,
      appSettings: api.settings.upsert,
    };

    const mut = mutationMap[table];
    if (!mut) {
      console.log(`  ⏭️  ${table}: skipped (no batch mutation)`);
      continue;
    }

    let success = 0;
    for (const record of records) {
      try {
        if (table === "appSettings") {
          await convex.mutation(mut, {
            key: record.settingKey,
            value: record.settingValue,
            settingType: record.settingType,
            category: record.category,
            description: record.description,
          });
        } else {
          await convex.mutation(mut, record);
        }
        success++;
      } catch (e: any) {
        // Skip duplicates silently
        if (!e.message?.includes("already exists")) {
          console.error(`  ⚠️  ${table}: ${e.message}`);
        }
      }
    }
    console.log(`  ✅ ${table}: ${success}/${records.length}`);
  }

  console.log("\n✅ Batch seed complete!");
}

seed().catch(console.error);
