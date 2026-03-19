/**
 * Revenue calculator for JESUS Company Cash Management System.
 * Calculates projected revenue inflows based on customer contracts and payment terms.
 *
 * Port of projection_engine/revenue_calculator.py
 */
import Decimal from 'decimal.js';
import { addDays, addMonths } from 'date-fns';
import { PAYMENT_PLAN_FREQUENCIES, DEFAULT_PAYMENT_TERMS } from '../constants';
import { utcDate, getUTCParts, getDaysInUTCMonth } from './date-utils';

export interface RevenueEventData {
  date: Date;
  customerId: number | string;
  companyName: string;
  amount: Decimal;
  entity: string;
  eventType: string;
  paymentPlan: string;
  invoiceDate: Date | null;
}

export interface CustomerContractData {
  id: number | string;
  companyName: string;
  monthlyFee: Decimal;
  paymentPlan: string;
  contractStart: Date;
  contractEnd: Date | null;
  status: string;
  entity: string;
  invoiceDay: number | null;
  paymentTermsDays: number | null;
  reliabilityScore: Decimal;
}

export interface PaymentOverrideData {
  contractId: number | string;
  originalDate: Date;
  newDate: Date | null;
  action: string;
}

export class RevenueCalculator {
  private paymentDelayDays: number;

  constructor(
    scenarioType: string = 'realistic',
    realisticDelayDays: number = DEFAULT_PAYMENT_TERMS.realisticDelayDays
  ) {
    this.paymentDelayDays = scenarioType === 'optimistic' ? 0 : realisticDelayDays;
  }

  calculatePaymentDate(billingMonth: Date, contractStart: Date, invoiceDay: number | null = null): Date {
    const { year, month } = getUTCParts(billingMonth);
    let paymentDay = invoiceDay ?? contractStart.getUTCDate();

    // Cap at max days in the billing month
    const maxDay = getDaysInUTCMonth(billingMonth);
    paymentDay = Math.min(paymentDay, maxDay);

    const basePaymentDate = utcDate(year, month, paymentDay);
    return addDays(basePaymentDate, this.paymentDelayDays);
  }

  getBillingMonths(contract: CustomerContractData, startDate: Date, endDate: Date): Date[] {
    const billingMonths: Date[] = [];
    const frequencyMonths = PAYMENT_PLAN_FREQUENCIES[contract.paymentPlan] ?? 1;

    const cs = getUTCParts(contract.contractStart);
    const ss = getUTCParts(startDate);

    let currentMonth = utcDate(cs.year, cs.month, 1);
    const projStart = utcDate(ss.year, ss.month, 1);
    if (projStart > currentMonth) currentMonth = projStart;

    const ee = getUTCParts(endDate);
    let endMonth: Date;
    if (contract.contractEnd) {
      const ce = getUTCParts(contract.contractEnd);
      const contractEndMonth = utcDate(ce.year, ce.month, 1);
      const projEndMonth = utcDate(ee.year, ee.month, 1);
      endMonth = contractEndMonth < projEndMonth ? contractEndMonth : projEndMonth;
    } else {
      endMonth = utcDate(ee.year, ee.month, 1);
    }

    while (currentMonth <= endMonth) {
      billingMonths.push(new Date(currentMonth));
      currentMonth = addMonths(currentMonth, frequencyMonths);
    }

    return billingMonths;
  }

  calculateRevenueEvents(
    contracts: CustomerContractData[],
    startDate: Date,
    endDate: Date,
    paymentOverrides: PaymentOverrideData[] = []
  ): RevenueEventData[] {
    const events: RevenueEventData[] = [];

    const overrideLookup = new Map<string, PaymentOverrideData>();
    for (const override of paymentOverrides) {
      const key = `${override.contractId}_${override.originalDate.toISOString().split('T')[0]}`;
      overrideLookup.set(key, override);
    }

    for (const contract of contracts) {
      if (contract.status !== 'Active') continue;

      const billingMonths = this.getBillingMonths(contract, startDate, endDate);

      for (const billingMonth of billingMonths) {
        let paymentDate = this.calculatePaymentDate(
          billingMonth,
          contract.contractStart,
          contract.invoiceDay
        );

        const overrideKey = `${contract.id}_${paymentDate.toISOString().split('T')[0]}`;
        const override = overrideLookup.get(overrideKey);

        if (override) {
          if (override.action === 'skip') continue;
          if (override.action === 'move' && override.newDate) {
            paymentDate = override.newDate;
          }
        }

        if (paymentDate >= startDate && paymentDate <= endDate) {
          const frequencyMonths = PAYMENT_PLAN_FREQUENCIES[contract.paymentPlan] ?? 1;
          const paymentAmount = contract.monthlyFee.mul(frequencyMonths);

          events.push({
            date: paymentDate,
            customerId: contract.id,
            companyName: contract.companyName,
            amount: paymentAmount,
            entity: contract.entity,
            eventType: 'payment',
            paymentPlan: contract.paymentPlan,
            invoiceDate: null,
          });
        }
      }
    }

    events.sort((a, b) => a.date.getTime() - b.date.getTime());
    return events;
  }

  calculateTotalRevenueByPeriod(
    events: RevenueEventData[],
    startDate: Date,
    endDate: Date,
    entity?: string
  ): Decimal {
    let total = new Decimal(0);
    for (const event of events) {
      if (event.date >= startDate && event.date <= endDate) {
        if (!entity || event.entity === entity) {
          total = total.add(event.amount);
        }
      }
    }
    return total;
  }
}
