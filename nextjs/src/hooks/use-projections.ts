'use client';

import { useQuery } from 'convex/react';
import { useMemo } from 'react';
import { api } from '../../convex/_generated/api';
import type { Doc } from '../../convex/_generated/dataModel';
import type { FunctionReturnType } from 'convex/server';
import Decimal from 'decimal.js';
import { addDays } from 'date-fns';
import { CashProjector, type AdhocEventData } from '@/lib/engine/cash-projector';
import type {
  CustomerContractData,
  PaymentOverrideData,
} from '@/lib/engine/revenue-calculator';
import type {
  VendorContractData,
  VendorPaymentOverrideData,
} from '@/lib/engine/expense-scheduler';
import { parseDate, formatDateISO } from '@/lib/engine/date-utils';
import type { Timeframe, ScenarioType } from '@/lib/types';
import { useAppStore } from '@/stores/app-store';

// Each timeframe shows a sensible range for its granularity
const TIMEFRAME_DAYS: Record<string, number> = {
  daily: 60,
  weekly: 180,
  monthly: 365,
  quarterly: 1095,
};

const DEFAULT_ACCOUNT = 'Main Account';

type ProjectionResponse = FunctionReturnType<typeof api.projections.getProjectionData>;
type ProjectionEntity = ProjectionResponse['entities'][number];
type CustomerDoc = Doc<'customerContracts'>;
type VendorDoc = Doc<'vendorContracts'>;
type OverrideDoc = Doc<'paymentOverrides'>;
type AdhocDoc = Doc<'adhocEvents'>;

type AccountSelection = { entity: string; accountName: string };

/**
 * Convert one entity's Convex documents into the engine's input shape.
 * Used by both the single-entity and consolidated projection paths
 * so they cannot drift.
 */
function reshapeEntityForEngine(
  entityData: ProjectionEntity,
  selectedAccountNames: string[] | undefined
): {
  customers: CustomerContractData[];
  vendors: VendorContractData[];
  customerOverrides: PaymentOverrideData[];
  vendorOverrides: VendorPaymentOverrideData[];
  adhocEvents: AdhocEventData[];
} {
  const filterByAccount = <T extends { bankAccount?: string }>(items: T[]): T[] => {
    if (!selectedAccountNames || selectedAccountNames.length === 0) return items;
    return items.filter((item) =>
      selectedAccountNames.includes(item.bankAccount ?? DEFAULT_ACCOUNT)
    );
  };

  const customers: CustomerContractData[] = filterByAccount(
    entityData.customers as CustomerDoc[]
  ).map((c) => ({
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

  const vendors: VendorContractData[] = filterByAccount(
    entityData.vendors as VendorDoc[]
  ).map((v) => ({
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

  const reshapeOverride = (o: OverrideDoc) => ({
    contractId: o.contractId,
    originalDate: parseDate(o.originalDate),
    newDate: o.newDate ? parseDate(o.newDate) : null,
    action: o.action,
  });

  const adhocEvents: AdhocEventData[] = filterByAccount(
    (entityData.adhocEvents ?? []) as AdhocDoc[]
  ).map((a) => ({
    id: a._id,
    eventType: (a.eventType === 'inflow' ? 'inflow' : 'outflow') as 'inflow' | 'outflow',
    date: parseDate(a.date),
    amount: new Decimal(a.amount),
    description: a.description,
    category: a.category,
    entity: a.entity,
    bankAccount: a.bankAccount,
    confidence: a.confidence,
  }));

  return {
    customers,
    vendors,
    customerOverrides: (entityData.customerOverrides as OverrideDoc[]).map(reshapeOverride),
    vendorOverrides: (entityData.vendorOverrides as OverrideDoc[]).map(reshapeOverride),
    adhocEvents,
  };
}

function accountNamesForEntity(
  entityCode: string,
  selectedAccounts: AccountSelection[],
  allAccountsSelected: boolean
): string[] | undefined {
  if (allAccountsSelected || selectedAccounts.length === 0) return undefined;
  const names = selectedAccounts
    .filter((a) => a.entity === entityCode)
    .map((a) => a.accountName);
  return names.length > 0 ? names : undefined;
}

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
  const {
    selectedAccounts,
    allAccountsSelected,
    customRangeStart,
    customRangeEnd,
  } = useAppStore();

  // Read configurable delay days from settings
  const delaySetting = useQuery(api.settings.getByKey, { key: 'realistic_delay_days' });
  const realisticDelayDays = delaySetting?.settingValue ? Number(delaySetting.settingValue) : 10;

  const queryArgs =
    allAccountsSelected || selectedAccounts.length === 0
      ? {}
      : { accounts: selectedAccounts };

  const data = useQuery(api.projections.getProjectionData, queryArgs);

  const projection = useMemo(() => {
    if (!data || data.entities.length === 0) {
      return { dataPoints: [], revenueEvents: [], expenseEvents: [] };
    }

    // Use the latest balance date as start, or today if none
    const balanceDateMs = data.entities
      .map((e) => e.balanceDate)
      .filter((d): d is string => Boolean(d))
      .map((d) => parseDate(d).getTime());
    const defaultStart = balanceDateMs.length > 0
      ? new Date(Math.max(...balanceDateMs))
      : parseDate(formatDateISO(new Date()));

    // Custom range overrides the timeframe preset when both ends are set.
    // We never start the engine earlier than the latest balance date —
    // events before that are assumed already reflected in the cash.
    const hasCustomRange = Boolean(customRangeStart && customRangeEnd);
    const startDate = hasCustomRange
      ? (() => {
          const customStart = parseDate(customRangeStart!);
          return customStart > defaultStart ? customStart : defaultStart;
        })()
      : defaultStart;
    const endDate = hasCustomRange
      ? parseDate(customRangeEnd!)
      : addDays(defaultStart, TIMEFRAME_DAYS[timeframe] ?? 365);
    // Events before today are already reflected in the bank balance
    const today = parseDate(formatDateISO(new Date()));
    const projector = new CashProjector();

    // Single-entity path
    if (data.entities.length === 1) {
      const ent = data.entities[0];
      const accountNames = accountNamesForEntity(
        ent.entity,
        selectedAccounts,
        allAccountsSelected
      );
      const reshaped = reshapeEntityForEngine(ent, accountNames);
      const result = projector.calculateProjectionDetailed({
        startDate,
        endDate,
        entity: ent.entity,
        timeframe,
        scenarioType,
        realisticDelayDays,
        projectionAsOfDate: today,
        startingCash: new Decimal(ent.startingCash),
        customerContracts: reshaped.customers,
        vendorContracts: reshaped.vendors,
        customerOverrides: reshaped.customerOverrides,
        vendorOverrides: reshaped.vendorOverrides,
        adhocEvents: reshaped.adhocEvents,
      });
      return serializeProjectionResult(result, ent.entity);
    }

    // Consolidated path — merge all entities and run a single projection
    // so endingCash is the total across selected accounts.
    const merged = {
      customers: [] as CustomerContractData[],
      vendors: [] as VendorContractData[],
      customerOverrides: [] as PaymentOverrideData[],
      vendorOverrides: [] as VendorPaymentOverrideData[],
      adhocEvents: [] as AdhocEventData[],
    };
    let totalStartingCash = new Decimal(0);

    for (const ent of data.entities) {
      const accountNames = accountNamesForEntity(
        ent.entity,
        selectedAccounts,
        allAccountsSelected
      );
      const reshaped = reshapeEntityForEngine(ent, accountNames);
      merged.customers.push(...reshaped.customers);
      merged.vendors.push(...reshaped.vendors);
      merged.customerOverrides.push(...reshaped.customerOverrides);
      merged.vendorOverrides.push(...reshaped.vendorOverrides);
      merged.adhocEvents.push(...reshaped.adhocEvents);
      totalStartingCash = totalStartingCash.add(ent.startingCash);
    }

    const result = projector.calculateProjectionDetailed({
      startDate,
      endDate,
      entity: 'Consolidated',
      timeframe,
      scenarioType,
      realisticDelayDays,
      projectionAsOfDate: today,
      startingCash: totalStartingCash,
      customerContracts: merged.customers,
      vendorContracts: merged.vendors,
      customerOverrides: merged.customerOverrides,
      vendorOverrides: merged.vendorOverrides,
      adhocEvents: merged.adhocEvents,
    });
    return serializeProjectionResult(result, 'Consolidated');
  }, [data, timeframe, scenarioType, allAccountsSelected, selectedAccounts, realisticDelayDays, customRangeStart, customRangeEnd]);

  const balanceDate = useMemo(() => {
    if (!data || data.entities.length === 0) return null;
    const dates = data.entities
      .map((e) => e.balanceDate)
      .filter((d): d is string => Boolean(d));
    return dates.sort().reverse()[0] ?? null;
  }, [data]);

  return {
    data: projection,
    isLoading: data === undefined,
    balanceDate,
  };
}

type EngineResult = ReturnType<CashProjector['calculateProjectionDetailed']>;

function serializeProjectionResult(result: EngineResult, fallbackEntity: string) {
  return {
    dataPoints: result.dataPoints.map((dp) => ({
      date: formatDateISO(dp.date),
      startingCash: dp.startingCash.toFixed(2),
      inflows: dp.inflows.toFixed(2),
      outflows: dp.outflows.toFixed(2),
      endingCash: dp.endingCash.toFixed(2),
      entity: dp.entity ?? fallbackEntity,
      timeframe: dp.timeframe,
      scenarioType: dp.scenarioType,
      isNegative: dp.isNegative,
    })),
    revenueEvents: result.revenueEvents.map((e) => ({
      date: formatDateISO(e.date),
      customerId: e.customerId,
      companyName: e.companyName,
      amount: e.amount.toFixed(2),
      entity: e.entity,
      eventType: e.eventType,
      paymentPlan: e.paymentPlan,
    })),
    expenseEvents: result.expenseEvents.map((e) => ({
      date: formatDateISO(e.date),
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
