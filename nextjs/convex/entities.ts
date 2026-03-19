import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  handler: async (ctx) => {
    return await ctx.db.query("entities").collect();
  },
});

export const getActive = query({
  handler: async (ctx) => {
    return (await ctx.db.query("entities").collect()).filter(
      (e) => e.isActive
    );
  },
});

export const create = mutation({
  args: {
    shortCode: v.string(),
    fullName: v.string(),
    color: v.optional(v.string()),
    displayOrder: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("entities")
      .withIndex("by_shortCode", (q) => q.eq("shortCode", args.shortCode))
      .first();
    if (existing) throw new Error(`Entity "${args.shortCode}" already exists`);

    return await ctx.db.insert("entities", {
      shortCode: args.shortCode,
      fullName: args.fullName,
      isActive: true,
      displayOrder: args.displayOrder ?? 0,
      color: args.color,
    });
  },
});

export const update = mutation({
  args: {
    id: v.id("entities"),
    shortCode: v.optional(v.string()),
    fullName: v.optional(v.string()),
    color: v.optional(v.string()),
    displayOrder: v.optional(v.number()),
    isActive: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    await ctx.db.patch(id, fields);
    return await ctx.db.get(id);
  },
});

export const remove = mutation({
  args: { id: v.id("entities") },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.id, { isActive: false });
  },
});
