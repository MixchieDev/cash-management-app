import { query } from "./_generated/server";
import { v } from "convex/values";

export const getActiveEntities = query({
  handler: async (ctx) => {
    return (await ctx.db.query("entities").collect()).filter((e) => e.isActive);
  },
});

// Get all accounts with latest balances (for account selector)
export const getAllAccountBalances = query({
  handler: async (ctx) => {
    const entities = (await ctx.db.query("entities").collect()).filter((e) => e.isActive);
    const result = [];

    for (const entity of entities) {
      const balances = await ctx.db
        .query("bankBalances")
        .withIndex("by_entity", (q: any) => q.eq("entity", entity.shortCode))
        .order("desc")
        .collect();

      // Group by accountName, take latest per account
      const latestByAccount = new Map<string, any>();
      for (const b of balances) {
        const name = b.accountName ?? "Main Account";
        if (!latestByAccount.has(name)) {
          latestByAccount.set(name, b);
        }
      }

      result.push({
        entity: entity.shortCode,
        fullName: entity.fullName,
        color: entity.color ?? "#64748b",
        accounts: Array.from(latestByAccount.entries()).map(([name, b]) => ({
          accountName: name,
          balance: b.balance,
          balanceDate: b.balanceDate,
        })),
      });
    }

    return result;
  },
});

// Get projection data — accepts specific accounts to include
export const getProjectionData = query({
  args: {
    accounts: v.optional(v.array(v.object({
      entity: v.string(),
      accountName: v.string(),
    }))),
  },
  handler: async (ctx, args) => {
    const activeEntities = (await ctx.db.query("entities").collect()).filter((e) => e.isActive);

    // Determine which entities to include
    let entityCodes: string[];
    if (args.accounts && args.accounts.length > 0) {
      entityCodes = [...new Set(args.accounts.map((a) => a.entity))];
    } else {
      // Consolidated — all active entities
      entityCodes = activeEntities.map((e) => e.shortCode);
    }

    const allData = [];
    for (const code of entityCodes) {
      const data = await getEntityData(ctx, code, args.accounts);
      if (data) allData.push(data);
    }

    return { consolidated: !args.accounts || args.accounts.length === 0, entities: allData };
  },
});

async function getEntityData(
  ctx: any,
  entity: string,
  selectedAccounts?: { entity: string; accountName: string }[]
) {
  // Get all balances for entity
  const allBalances = await ctx.db
    .query("bankBalances")
    .withIndex("by_entity", (q: any) => q.eq("entity", entity))
    .order("desc")
    .collect();

  // Group by account, take latest per account
  const latestByAccount = new Map<string, any>();
  for (const b of allBalances) {
    const name = b.accountName ?? "Main Account";
    if (!latestByAccount.has(name)) {
      latestByAccount.set(name, b);
    }
  }

  // Filter to selected accounts if specified
  let accountsToInclude: any[];
  if (selectedAccounts && selectedAccounts.length > 0) {
    const selectedForEntity = selectedAccounts
      .filter((a) => a.entity === entity)
      .map((a) => a.accountName);
    accountsToInclude = Array.from(latestByAccount.values()).filter(
      (b) => selectedForEntity.includes(b.accountName ?? "Main Account")
    );
  } else {
    accountsToInclude = Array.from(latestByAccount.values());
  }

  if (accountsToInclude.length === 0) return null;

  // Sum balances across selected accounts
  const startingCash = accountsToInclude.reduce((sum: number, b: any) => sum + b.balance, 0);
  const latestDate = accountsToInclude
    .map((b: any) => b.balanceDate)
    .sort()
    .reverse()[0];

  // Active customers
  const customers = await ctx.db
    .query("customerContracts")
    .withIndex("by_entity_status", (q: any) =>
      q.eq("entity", entity).eq("status", "Active")
    )
    .collect();

  // Active vendors
  const vendors = await ctx.db
    .query("vendorContracts")
    .withIndex("by_entity_status", (q: any) =>
      q.eq("entity", entity).eq("status", "Active")
    )
    .collect();

  // Payment overrides filtered by entity
  const allCustomerOverrides = await ctx.db
    .query("paymentOverrides")
    .withIndex("by_type", (q: any) => q.eq("overrideType", "customer"))
    .collect();
  const customerOverrides = allCustomerOverrides.filter((o: any) => o.entity === entity);

  const allVendorOverrides = await ctx.db
    .query("paymentOverrides")
    .withIndex("by_type", (q: any) => q.eq("overrideType", "vendor"))
    .collect();
  const vendorOverrides = allVendorOverrides.filter((o: any) => o.entity === entity);

  return {
    entity,
    startingCash,
    balanceDate: latestDate,
    accounts: accountsToInclude.map((b: any) => ({
      accountName: b.accountName ?? "Main Account",
      balance: b.balance,
    })),
    customers,
    vendors,
    customerOverrides,
    vendorOverrides,
  };
}
