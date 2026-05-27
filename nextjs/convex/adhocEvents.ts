import { query, mutation } from "./_generated/server";
import { v } from "convex/values";
import { validateAdhocEventInput } from "./adhocEventValidation";

export const list = query({
  args: { entity: v.optional(v.string()) },
  handler: async (ctx, args) => {
    if (args.entity) {
      return await ctx.db
        .query("adhocEvents")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .collect();
    }
    return await ctx.db.query("adhocEvents").collect();
  },
});

export const create = mutation({
  args: {
    eventType: v.string(),
    date: v.string(),
    amount: v.number(),
    description: v.string(),
    category: v.optional(v.string()),
    entity: v.string(),
    bankAccount: v.optional(v.string()),
    confidence: v.optional(v.string()),
    notes: v.optional(v.string()),
    createdBy: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const validation = validateAdhocEventInput(args);
    if (!validation.ok) {
      throw new Error(validation.error);
    }
    return await ctx.db.insert("adhocEvents", args);
  },
});

export const update = mutation({
  args: {
    id: v.id("adhocEvents"),
    eventType: v.optional(v.string()),
    date: v.optional(v.string()),
    amount: v.optional(v.number()),
    description: v.optional(v.string()),
    category: v.optional(v.string()),
    entity: v.optional(v.string()),
    bankAccount: v.optional(v.string()),
    confidence: v.optional(v.string()),
    notes: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    const existing = await ctx.db.get(id);
    if (!existing) {
      throw new Error("Ad-hoc event not found");
    }
    // Validate the merged shape so callers can patch any subset of fields.
    const merged = { ...existing, ...fields };
    const validation = validateAdhocEventInput({
      eventType: merged.eventType,
      date: merged.date,
      amount: merged.amount,
      description: merged.description,
      category: merged.category,
      entity: merged.entity,
      bankAccount: merged.bankAccount,
      confidence: merged.confidence,
      notes: merged.notes,
    });
    if (!validation.ok) {
      throw new Error(validation.error);
    }
    await ctx.db.patch(id, fields);
    return await ctx.db.get(id);
  },
});

export const remove = mutation({
  args: { id: v.id("adhocEvents") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
