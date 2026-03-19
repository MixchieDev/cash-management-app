import { query, mutation } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: { entity: v.optional(v.string()) },
  handler: async (ctx, args) => {
    let scenariosList;
    if (args.entity && args.entity !== "Consolidated") {
      scenariosList = await ctx.db
        .query("scenarios")
        .withIndex("by_entity", (q) => q.eq("entity", args.entity!))
        .collect();
    } else {
      scenariosList = await ctx.db.query("scenarios").collect();
    }

    // Attach changes to each scenario
    const results = await Promise.all(
      scenariosList.map(async (scenario) => {
        const changes = await ctx.db
          .query("scenarioChanges")
          .withIndex("by_scenarioId", (q) => q.eq("scenarioId", scenario._id))
          .collect();
        return { ...scenario, changes };
      })
    );

    return results;
  },
});

export const get = query({
  args: { id: v.id("scenarios") },
  handler: async (ctx, args) => {
    const scenario = await ctx.db.get(args.id);
    if (!scenario) return null;

    const changes = await ctx.db
      .query("scenarioChanges")
      .withIndex("by_scenarioId", (q) => q.eq("scenarioId", args.id))
      .collect();

    return { ...scenario, changes };
  },
});

export const create = mutation({
  args: {
    scenarioName: v.string(),
    entity: v.string(),
    description: v.optional(v.string()),
    createdBy: v.optional(v.string()),
    changes: v.array(
      v.object({
        changeType: v.string(),
        startDate: v.string(),
        endDate: v.optional(v.string()),
        employees: v.optional(v.number()),
        salaryPerEmployee: v.optional(v.number()),
        expenseName: v.optional(v.string()),
        expenseAmount: v.optional(v.number()),
        expenseFrequency: v.optional(v.string()),
        newClients: v.optional(v.number()),
        revenuePerClient: v.optional(v.number()),
        investmentAmount: v.optional(v.number()),
        lostRevenue: v.optional(v.number()),
        notes: v.optional(v.string()),
      })
    ),
  },
  handler: async (ctx, args) => {
    const { changes, ...scenarioData } = args;
    const scenarioId = await ctx.db.insert("scenarios", scenarioData);

    for (const change of changes) {
      await ctx.db.insert("scenarioChanges", { ...change, scenarioId });
    }

    return { _id: scenarioId, ...scenarioData };
  },
});

export const update = mutation({
  args: {
    id: v.id("scenarios"),
    scenarioName: v.optional(v.string()),
    description: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const { id, ...fields } = args;
    await ctx.db.patch(id, fields);
    return await ctx.db.get(id);
  },
});

export const remove = mutation({
  args: { id: v.id("scenarios") },
  handler: async (ctx, args) => {
    // Delete all changes first
    const changes = await ctx.db
      .query("scenarioChanges")
      .withIndex("by_scenarioId", (q) => q.eq("scenarioId", args.id))
      .collect();

    for (const change of changes) {
      await ctx.db.delete(change._id);
    }

    await ctx.db.delete(args.id);
  },
});
