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
    return await ctx.db
      .query("bankBalances")
      .withIndex("by_entity", (q) => q.eq("entity", args.entity))
      .order("desc")
      .first();
  },
});

// Get all accounts with their latest balance for an entity
export const getAccountBalances = query({
  args: { entity: v.string() },
  handler: async (ctx, args) => {
    const all = await ctx.db
      .query("bankBalances")
      .withIndex("by_entity", (q) => q.eq("entity", args.entity))
      .order("desc")
      .collect();

    // Group by accountName, take latest (first in desc order) per account
    const latestByAccount = new Map<string, typeof all[0]>();
    for (const b of all) {
      const name = b.accountName ?? "Main Account";
      if (!latestByAccount.has(name)) {
        latestByAccount.set(name, b);
      }
    }

    return Array.from(latestByAccount.values());
  },
});

// Get all unique account names across all entities (for autocomplete)
export const getAccountNames = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("bankBalances").collect();
    const names = new Set<string>();
    for (const b of all) {
      names.add(b.accountName ?? "Main Account");
    }
    return Array.from(names).sort();
  },
});

export const create = mutation({
  args: {
    balanceDate: v.string(),
    entity: v.string(),
    accountName: v.string(),
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
