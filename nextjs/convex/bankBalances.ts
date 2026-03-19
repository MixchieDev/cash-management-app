import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: { entity: v.optional(v.string()) },
  handler: async (ctx, args) => {
    if (args.entity) {
      return await ctx.db
        .query("bankBalances")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .order("desc")
        .collect();
    }
    return await ctx.db.query("bankBalances").order("desc").collect();
  },
});

export const getLatest = query({
  args: { entity: v.string() },
  handler: async (ctx, args) => {
    const results = await ctx.db
      .query("bankBalances")
      .withIndex("by_entity", (q) => q.eq("entity", args.entity))
      .order("desc")
      .first();
    return results;
  },
});

export const create = mutation({
  args: {
    balanceDate: v.string(),
    entity: v.string(),
    balance: v.number(),
    source: v.string(),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("bankBalances", args);
  },
});

export const remove = mutation({
  args: { id: v.id("bankBalances") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
