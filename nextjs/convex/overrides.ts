import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

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
    return await ctx.db.insert("paymentOverrides", args);
  },
});

export const remove = mutation({
  args: { id: v.id("paymentOverrides") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
