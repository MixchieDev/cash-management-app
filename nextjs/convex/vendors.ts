import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: { entity: v.optional(v.string()), status: v.optional(v.string()) },
  handler: async (ctx, args) => {
    let results;
    if (args.entity && args.status) {
      results = await ctx.db
        .query("vendorContracts")
        .withIndex("by_entity_status", (q) =>
          q.eq("entity", args.entity!).eq("status", args.status!)
        )
        .collect();
    } else if (args.entity) {
      results = await ctx.db
        .query("vendorContracts")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .collect();
    } else {
      results = await ctx.db.query("vendorContracts").collect();
    }
    return results;
  },
});

export const get = query({
  args: { id: v.id("vendorContracts") },
  handler: async (ctx, args) => {
    return await ctx.db.get(args.id);
  },
});

export const create = mutation({
  args: {
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
    bankAccount: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("vendorContracts", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("vendorContracts"),
    vendorName: v.optional(v.string()),
    category: v.optional(v.string()),
    amount: v.optional(v.number()),
    frequency: v.optional(v.string()),
    dueDate: v.optional(v.string()),
    startDate: v.optional(v.string()),
    endDate: v.optional(v.string()),
    entity: v.optional(v.string()),
    priority: v.optional(v.number()),
    flexibilityDays: v.optional(v.number()),
    status: v.optional(v.string()),
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
  args: { id: v.id("vendorContracts") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { status: "Inactive" });
  },
});

export const remove = mutation({
  args: { id: v.id("vendorContracts") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
