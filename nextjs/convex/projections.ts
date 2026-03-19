import { query } from "./_generated/server";
import { v } from "convex/values";

export const getActiveEntities = query({
  handler: async (ctx) => {
    return await ctx.db
      .query("entities")
      .filter((q) => q.eq(q.field("isActive"), true))
      .collect();
  },
});

export const getProjectionData = query({
  args: { entity: v.string() },
  handler: async (ctx, args) => {
    const entity = args.entity;

    if (entity === "Consolidated") {
      const activeEntities = await ctx.db
        .query("entities")
        .filter((q) => q.eq(q.field("isActive"), true))
        .collect();

      const entityCodes = activeEntities.map((e) => e.shortCode);
      const allData = [];

      for (const code of entityCodes) {
        const data = await getEntityData(ctx, code);
        if (data) allData.push(data);
      }

      return { consolidated: true, entities: allData };
    }

    const data = await getEntityData(ctx, entity);
    return data ? { consolidated: false, entities: [data] } : { consolidated: false, entities: [] };
  },
});

async function getEntityData(ctx: any, entity: string) {
  // Get ALL balances for this entity, then pick the one with latest balanceDate
  const allBalances = await ctx.db
    .query("bankBalances")
    .withIndex("by_entity_date", (q: any) => q.eq("entity", entity))
    .order("desc")
    .collect();

  // The index is (entity, balanceDate) so desc order gives latest balanceDate first
  const latestBalance = allBalances[0];
  if (!latestBalance) return null;

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

  // Payment overrides — filter by entity to avoid cross-entity contamination
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
    startingCash: latestBalance.balance,
    balanceDate: latestBalance.balanceDate,
    customers,
    vendors,
    customerOverrides,
    vendorOverrides,
  };
}
