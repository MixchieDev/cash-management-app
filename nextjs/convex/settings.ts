import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  handler: async (ctx) => {
    return await ctx.db.query("appSettings").collect();
  },
});

export const getByKey = query({
  args: { key: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("appSettings")
      .withIndex("by_key", (q) => q.eq("settingKey", args.key))
      .first();
  },
});

export const upsert = mutation({
  args: {
    key: v.string(),
    value: v.string(),
    settingType: v.optional(v.string()),
    category: v.optional(v.string()),
    description: v.optional(v.string()),
    updatedBy: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("appSettings")
      .withIndex("by_key", (q) => q.eq("settingKey", args.key))
      .first();

    if (existing) {
      // Log the change
      await ctx.db.insert("settingsAuditLog", {
        settingKey: args.key,
        oldValue: existing.settingValue,
        newValue: args.value,
        changedBy: args.updatedBy,
      });

      await ctx.db.patch(existing._id, {
        settingValue: args.value,
        updatedBy: args.updatedBy,
      });

      return existing._id;
    }

    return await ctx.db.insert("appSettings", {
      settingKey: args.key,
      settingValue: args.value,
      settingType: args.settingType ?? "string",
      category: args.category ?? "general",
      description: args.description,
      updatedBy: args.updatedBy,
    });
  },
});

export const getAuditLog = query({
  handler: async (ctx) => {
    return await ctx.db.query("settingsAuditLog").order("desc").take(100);
  },
});
