import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { api } from "./_generated/api";

const http = httpRouter();

// ═══════════════════════════════════════════════════════════════
// POST /sync-contract — Billing app → Cash Management sync
// ═══════════════════════════════════════════════════════════════
http.route({
  path: "/sync-contract",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    // Verify API key
    const apiKey = request.headers.get("x-api-key");
    const storedKey = await ctx.runQuery(api.settings.getByKey, { key: "sync_api_key" });

    if (!storedKey || !apiKey || apiKey !== storedKey.settingValue) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: corsHeaders(),
      });
    }

    try {
      const body = await request.json();

      // Validate required fields
      if (!body.customerNumber || !body.companyName || !body.entity) {
        return new Response(
          JSON.stringify({ error: "Missing required fields: customerNumber, companyName, entity" }),
          { status: 400, headers: corsHeaders() }
        );
      }

      // Map billing app status to cash management status
      const statusMap: Record<string, string> = {
        NOT_STARTED: "Pending",
        ACTIVE: "Active",
        PAUSED: "Inactive",
        CANCELLED: "Cancelled",
        COMPLETED: "Inactive",
        OVERDUE: "Active",
      };

      const result = await ctx.runMutation(api.customers.upsertByCustomerNumber, {
        customerNumber: body.customerNumber,
        companyName: body.companyName,
        monthlyFee: body.monthlyFee ?? 0,
        paymentPlan: mapPaymentPlan(body.paymentPlan),
        contractStart: body.contractStart ?? new Date().toISOString().split("T")[0],
        contractEnd: body.contractEndDate ?? undefined,
        status: statusMap[body.status] ?? "Active",
        whoAcquired: body.whoAcquired ?? body.partnerName ?? "",
        entity: body.entity,
        invoiceDay: body.billingDayOfMonth ?? undefined,
        reliabilityScore: 0.8,
        notes: body.remarks ?? undefined,
        bankAccount: body.bankAccount ?? "Main Account",
        externalId: body.id ?? undefined,
      });

      return new Response(JSON.stringify({ success: true, ...result }), {
        status: 200,
        headers: corsHeaders(),
      });
    } catch (err: any) {
      return new Response(
        JSON.stringify({ error: err.message ?? "Internal error" }),
        { status: 500, headers: corsHeaders() }
      );
    }
  }),
});

// ═══════════════════════════════════════════════════════════════
// POST /sync-contracts — Batch sync multiple contracts
// ═══════════════════════════════════════════════════════════════
http.route({
  path: "/sync-contracts",
  method: "POST",
  handler: httpAction(async (ctx, request) => {
    const apiKey = request.headers.get("x-api-key");
    const storedKey = await ctx.runQuery(api.settings.getByKey, { key: "sync_api_key" });

    if (!storedKey || !apiKey || apiKey !== storedKey.settingValue) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: corsHeaders(),
      });
    }

    try {
      const body = await request.json();
      const contracts = body.contracts;

      if (!Array.isArray(contracts)) {
        return new Response(
          JSON.stringify({ error: "Expected { contracts: [...] }" }),
          { status: 400, headers: corsHeaders() }
        );
      }

      const statusMap: Record<string, string> = {
        NOT_STARTED: "Pending",
        ACTIVE: "Active",
        PAUSED: "Inactive",
        CANCELLED: "Cancelled",
        COMPLETED: "Inactive",
        OVERDUE: "Active",
      };

      let created = 0;
      let updated = 0;
      let skipped = 0;

      for (const c of contracts) {
        if (!c.customerNumber || !c.companyName || !c.entity) {
          skipped++;
          continue;
        }

        const result = await ctx.runMutation(api.customers.upsertByCustomerNumber, {
          customerNumber: c.customerNumber,
          companyName: c.companyName,
          monthlyFee: c.monthlyFee ?? 0,
          paymentPlan: mapPaymentPlan(c.paymentPlan),
          contractStart: c.contractStart ?? new Date().toISOString().split("T")[0],
          contractEnd: c.contractEndDate ?? undefined,
          status: statusMap[c.status] ?? "Active",
          whoAcquired: c.whoAcquired ?? c.partnerName ?? "",
          entity: c.entity,
          invoiceDay: c.billingDayOfMonth ?? undefined,
          reliabilityScore: 0.8,
          notes: c.remarks ?? undefined,
          bankAccount: c.bankAccount ?? "Main Account",
          externalId: c.id ?? undefined,
        });

        if (result.action === "created") created++;
        else updated++;
      }

      return new Response(
        JSON.stringify({ success: true, created, updated, skipped, total: contracts.length }),
        { status: 200, headers: corsHeaders() }
      );
    } catch (err: any) {
      return new Response(
        JSON.stringify({ error: err.message ?? "Internal error" }),
        { status: 500, headers: corsHeaders() }
      );
    }
  }),
});

// CORS preflight for both endpoints
http.route({
  path: "/sync-contract",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }),
});

http.route({
  path: "/sync-contracts",
  method: "OPTIONS",
  handler: httpAction(async () => {
    return new Response(null, { status: 204, headers: corsHeaders() });
  }),
});

function corsHeaders(): HeadersInit {
  return {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, x-api-key",
  };
}

function mapPaymentPlan(plan?: string): string {
  if (!plan) return "Monthly";
  const map: Record<string, string> = {
    MONTHLY: "Monthly",
    QUARTERLY: "Quarterly",
    SEMI_ANNUALLY: "Bi-annually",
    ANNUALLY: "Annual",
    ANNUAL: "Annual",
    ONE_TIME: "Monthly",
  };
  return map[plan.toUpperCase()] ?? plan;
}

export default http;
