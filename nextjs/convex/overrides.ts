import { query, mutation } from "./_generated/server";
import { v } from "convex/values";
import { validateOverrideInput } from "./overrideValidation";

export const list = query({
  args: {
    overrideType: v.optional(v.string()),
    entity: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    if (args.overrideType) {
      return await ctx.db
        .query("paymentOverrides")
        .withIndex("by_type", (q) => q.eq("overrideType", args.overrideType!))
        .collect();
    }
    if (args.entity) {
      return await ctx.db
        .query("paymentOverrides")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .collect();
    }
    return await ctx.db.query("paymentOverrides").collect();
  },
});

export const create = mutation({
  args: {
    overrideType: v.string(),
    contractId: v.string(),
    originalDate: v.string(),
    newDate: v.optional(v.string()),
    action: v.string(),
    entity: v.string(),
    reason: v.optional(v.string()),
    createdBy: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // 1. Shape validation (pure)
    const validation = validateOverrideInput(args);
    if (!validation.ok) {
      throw new Error(validation.error);
    }

    // 2. Foreign-key check: the contract must exist AND live in the table
    //    that matches overrideType. Convex IDs are not table-scoped at runtime,
    //    so `db.get` would happily return a customer doc for a vendor override;
    //    `normalizeId` checks the table prefix on the ID itself.
    const tableName =
      args.overrideType === "customer" ? "customerContracts" : "vendorContracts";
    const normalizedId = ctx.db.normalizeId(tableName, args.contractId);
    if (!normalizedId) {
      throw new Error(
        `${args.overrideType === "customer" ? "Customer" : "Vendor"} contract not found for the selected override`
      );
    }
    const contract = await ctx.db.get(normalizedId);
    if (!contract) {
      throw new Error(
        `${args.overrideType === "customer" ? "Customer" : "Vendor"} contract not found for the selected override`
      );
    }
    if (contract.entity !== args.entity) {
      throw new Error(
        `Override entity (${args.entity}) does not match contract entity (${contract.entity})`
      );
    }

    // 3. Duplicate check: only one override allowed per (contract, originalDate)
    const existing = await ctx.db
      .query("paymentOverrides")
      .withIndex("by_type", (q) => q.eq("overrideType", args.overrideType))
      .filter((q) =>
        q.and(
          q.eq(q.field("contractId"), args.contractId),
          q.eq(q.field("originalDate"), args.originalDate)
        )
      )
      .first();
    if (existing) {
      throw new Error(
        "An override already exists for this payment. Remove the existing one first."
      );
    }

    return await ctx.db.insert("paymentOverrides", args);
  },
});

export const remove = mutation({
  args: { id: v.id("paymentOverrides") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
