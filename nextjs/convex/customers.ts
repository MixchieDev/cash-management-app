import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: { entity: v.optional(v.string()), status: v.optional(v.string()) },
  handler: async (ctx, args) => {
    let results;
    if (args.entity && args.status) {
      results = await ctx.db
        .query("customerContracts")
        .withIndex("by_entity_status", (q) =>
          q.eq("entity", args.entity!).eq("status", args.status!)
        )
        .collect();
    } else if (args.entity) {
      results = await ctx.db
        .query("customerContracts")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .collect();
    } else if (args.status) {
      results = await ctx.db
        .query("customerContracts")
        .withIndex("by_status", (q) => q.eq("status", args.status!))
        .collect();
    } else {
      results = await ctx.db.query("customerContracts").collect();
    }
    return results;
  },
});

export const get = query({
  args: { id: v.id("customerContracts") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
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
    bankAccount: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("customerContracts", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("customerContracts"),
    companyName: v.optional(v.string()),
    monthlyFee: v.optional(v.number()),
    paymentPlan: v.optional(v.string()),
    contractStart: v.optional(v.string()),
    contractEnd: v.optional(v.string()),
    status: v.optional(v.string()),
    whoAcquired: v.optional(v.string()),
    entity: v.optional(v.string()),
    invoiceDay: v.optional(v.number()),
    paymentTermsDays: v.optional(v.number()),
    reliabilityScore: v.optional(v.number()),
    notes: v.optional(v.string()),
    bankAccount: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    await ctx.db.patch(id, fields);
    return await ctx.db.get(id);
  },
});

export const deactivate = mutation({
  args: { id: v.id("customerContracts") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { status: "Inactive" });
  },
});

export const remove = mutation({
  args: { id: v.id("customerContracts") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
