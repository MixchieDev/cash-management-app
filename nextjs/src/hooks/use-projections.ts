'use client';

import { useQuery } from 'convex/react';
import { useMemo } from 'react';
import { api } from '../../convex/_generated/api';
import Decimal from 'decimal.js';
import { addDays } from 'date-fns';
import { CashProjector } from '@/lib/engine/cash-projector';
import type { CustomerContractData } from '@/lib/engine/revenue-calculator';
import type { VendorContractData } from '@/lib/engine/expense-scheduler';
import { parseDate } from '@/lib/engine/date-utils';
import type { Timeframe, ScenarioType } from '@/lib/types';
import { useAppStore, type SelectedAccount } from '@/stores/app-store';

// Each timeframe shows a sensible range for its granularity
const TIMEFRAME_DAYS: Record<string, number> = {
  daily: 60,
  weekly: 180,
  monthly: 365,
  quarterly: 1095,
};

/**
 * Reactive projection hook.
 * Convex provides real-time contract/balance data.
 * The projection engine runs client-side (pure TypeScript, no DB calls).
 */
export function useProjection(
  _entity: string, // kept for backward compat, actual selection from store
  timeframe: Timeframe,
  scenarioType: ScenarioType
) {
  const { selectedAccounts, allAccountsSelected } = useAppStore();

  // Pass selected accounts to Convex, or undefined for consolidated
  const queryArgs = allAccountsSelected || selectedAccounts.length === 0
    ? {}
    : { accounts: selectedAccounts };

  const data = useQuery(api.projections.getProjectionData, queryArgs);

  const projection = useMemo(() => {
    if (!data || data.entities.length === 0) {
      return { dataPoints: [], revenueEvents: [], expenseEvents: [] };
    }

    // Use the latest balance date as start, or today if none
    const balanceDates = data.entities
      .map((e: any) => e.balanceDate)
      .filter(Boolean)
      .map((d: string) => parseDate(d));
    const startDate = balanceDates.length > 0
      ? new Date(Math.max(...balanceDates.map((d: Date) => d.getTime())))
      : parseDate(new Date().toISOString().split('T')[0]);
    const endDate = addDays(startDate, TIMEFRAME_DAYS[timeframe] ?? 365);
    const projector = new CashProjector();

    // Get selected account names per entity for contract filtering
    const getAccountNamesForEntity = (entityCode: string): string[] | undefined => {
      if (allAccountsSelected || selectedAccounts.length === 0) return undefined;
      const names = selectedAccounts
        .filter((a) => a.entity === entityCode)
        .map((a) => a.accountName);
      return names.length > 0 ? names : undefined;
    };

    if (data.entities.length === 1) {
      const ent = data.entities[0];
      return runProjection(projector, ent, startDate, endDate, timeframe, scenarioType, getAccountNamesForEntity(ent.entity));
    }

    // Consolidated: run per entity and merge
    let mergedDataPoints: ReturnType<typeof runProjection>['dataPoints'] | null = null;
    let allRevenue: ReturnType<typeof runProjection>['revenueEvents'] = [];
    let allExpenses: ReturnType<typeof runProjection>['expenseEvents'] = [];

    for (const ent of data.entities) {
      const result = runProjection(projector, ent, startDate, endDate, timeframe, scenarioType, getAccountNamesForEntity(ent.entity));

      allRevenue = [...allRevenue, ...result.revenueEvents];
      allExpenses = [...allExpenses, ...result.expenseEvents];

      if (!mergedDataPoints) {
        mergedDataPoints = result.dataPoints;
      } else {
        for (let i = 0; i < result.dataPoints.length && i < mergedDataPoints.length; i++) {
          const m = mergedDataPoints[i];
          const r = result.dataPoints[i];
          const newEndingCash = new Decimal(m.endingCash).add(r.endingCash);
          mergedDataPoints[i] = {
            ...m,
            startingCash: new Decimal(m.startingCash).add(r.startingCash).toFixed(2),
            inflows: new Decimal(m.inflows).add(r.inflows).toFixed(2),
            outflows: new Decimal(m.outflows).add(r.outflows).toFixed(2),
            endingCash: newEndingCash.toFixed(2),
            entity: 'Consolidated',
            isNegative: newEndingCash.isNegative(),
          } as any;
        }
      }
    }

    return {
      dataPoints: (mergedDataPoints ?? []).map((dp: any) => ({
        ...dp,
        entity: 'Consolidated',
      })),
      revenueEvents: allRevenue,
      expenseEvents: allExpenses,
    };
  }, [data, timeframe, scenarioType]);

  // Extract the balance date for display
  const balanceDate = useMemo(() => {
    if (!data || data.entities.length === 0) return null;
    const dates = data.entities.map((e: any) => e.balanceDate).filter(Boolean) as string[];
    return dates.sort().reverse()[0] ?? null;
  }, [data]);

  return {
    data: projection,
    isLoading: data === undefined,
    balanceDate,
  };
}

function runProjection(
  projector: CashProjector,
  entityData: any,
  startDate: Date,
  endDate: Date,
  timeframe: string,
  scenarioType: string,
  selectedAccountNames?: string[]
) {
  // Filter contracts by bank account if specific accounts are selected
  const filterByAccount = (contracts: any[]) => {
    if (!selectedAccountNames || selectedAccountNames.length === 0) return contracts;
    return contracts.filter((c: any) => {
      const account = c.bankAccount ?? 'RCBC Current';
      return selectedAccountNames.includes(account);
    });
  };

  const filteredCustomers = filterByAccount(entityData.customers);
  const filteredVendors = filterByAccount(entityData.vendors);

  const customerContracts: CustomerContractData[] = filteredCustomers.map((c: any) => ({
    id: c._id,
    companyName: c.companyName,
    monthlyFee: new Decimal(c.monthlyFee),
    paymentPlan: c.paymentPlan,
    contractStart: parseDate(c.contractStart),
    contractEnd: c.contractEnd ? parseDate(c.contractEnd) : null,
    status: c.status,
    entity: c.entity,
    invoiceDay: c.invoiceDay ?? null,
    paymentTermsDays: c.paymentTermsDays ?? null,
    reliabilityScore: new Decimal(c.reliabilityScore),
  }));

  const vendorContracts: VendorContractData[] = filteredVendors.map((v: any) => ({
    id: v._id,
    vendorName: v.vendorName,
    category: v.category,
    amount: new Decimal(v.amount),
    frequency: v.frequency,
    dueDate: parseDate(v.dueDate),
    startDate: v.startDate ? parseDate(v.startDate) : null,
    endDate: v.endDate ? parseDate(v.endDate) : null,
    entity: v.entity,
    priority: v.priority,
    flexibilityDays: v.flexibilityDays,
    status: v.status,
  }));

  const result = projector.calculateProjectionDetailed({
    startDate,
    endDate,
    entity: entityData.entity,
    timeframe,
    scenarioType,
    startingCash: new Decimal(entityData.startingCash),
    customerContracts,
    vendorContracts,
    customerOverrides: entityData.customerOverrides.map((o: any) => ({
      contractId: o.contractId,
      originalDate: parseDate(o.originalDate),
      newDate: o.newDate ? parseDate(o.newDate) : null,
      action: o.action,
    })),
    vendorOverrides: entityData.vendorOverrides.map((o: any) => ({
      contractId: o.contractId,
      originalDate: parseDate(o.originalDate),
      newDate: o.newDate ? parseDate(o.newDate) : null,
      action: o.action,
    })),
  });

  // Serialize for component consumption
  return {
    dataPoints: result.dataPoints.map((dp) => ({
      date: dp.date.toISOString().split('T')[0],
      startingCash: dp.startingCash.toFixed(2),
      inflows: dp.inflows.toFixed(2),
      outflows: dp.outflows.toFixed(2),
      endingCash: dp.endingCash.toFixed(2),
      entity: dp.entity,
      timeframe: dp.timeframe,
      scenarioType: dp.scenarioType,
      isNegative: dp.isNegative,
    })),
    revenueEvents: result.revenueEvents.map((e) => ({
      date: e.date.toISOString().split('T')[0],
      customerId: e.customerId,
      companyName: e.companyName,
      amount: e.amount.toFixed(2),
      entity: e.entity,
      eventType: e.eventType,
      paymentPlan: e.paymentPlan,
    })),
    expenseEvents: result.expenseEvents.map((e) => ({
      date: e.date.toISOString().split('T')[0],
      vendorId: e.vendorId,
      vendorName: e.vendorName,
      amount: e.amount.toFixed(2),
      entity: e.entity,
      category: e.category,
      priority: e.priority,
      isPayroll: e.isPayroll,
    })),
  };
}
