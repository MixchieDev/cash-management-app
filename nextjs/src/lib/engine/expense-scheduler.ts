/**
 * Expense scheduler for JESUS Company Cash Management System.
 * Schedules expense outflows from vendor contracts.
 *
 * Port of projection_engine/expense_scheduler.py
 */
import Decimal from 'decimal.js';
import { addDays, addMonths, addYears } from 'date-fns';

export interface ExpenseEventData {
  date: Date;
  vendorId: number | string | null;
  vendorName: string;
  amount: Decimal;
  entity: string;
  category: string;
  priority: number;
  isPayroll: boolean;
}

export interface VendorContractData {
  id: number | string;
  vendorName: string;
  category: string;
  amount: Decimal;
  frequency: string;
  dueDate: Date;
  startDate: Date | null;
  endDate: Date | null;
  entity: string;
  priority: number;
  flexibilityDays: number;
  status: string;
}

export interface VendorPaymentOverrideData {
  contractId: number | string;
  originalDate: Date;
  newDate: Date | null;
  action: string;
}

function addFrequency(d: Date, frequency: string): Date {
  switch (frequency) {
    case 'Daily': return addDays(d, 1);
    case 'Weekly': return addDays(d, 7);
    case 'Bi-weekly': return addDays(d, 14);
    case 'Monthly': return addMonths(d, 1);
    case 'Quarterly': return addMonths(d, 3);
    case 'Annual': return addYears(d, 1);
    default: return addDays(d, 30);
  }
}

export class ExpenseScheduler {
  getVendorPaymentDates(
    contract: VendorContractData,
    startDate: Date,
    endDate: Date
  ): Date[] {
    const paymentDates: Date[] = [];

    const effectiveStartDate = contract.startDate && contract.startDate > startDate
      ? contract.startDate
      : startDate;

    const effectiveEndDate = contract.endDate && contract.endDate < endDate
      ? contract.endDate
      : endDate;

    if (effectiveStartDate > effectiveEndDate) return paymentDates;

    // One-time payment
    if (contract.frequency === 'One-time') {
      if (contract.dueDate >= effectiveStartDate && contract.dueDate <= effectiveEndDate) {
        paymentDates.push(contract.dueDate);
      }
      return paymentDates;
    }

    // Recurring: fast-forward from dueDate to effective start
    let currentDate = new Date(contract.dueDate.getTime());
    while (currentDate < effectiveStartDate) {
      currentDate = addFrequency(currentDate, contract.frequency);
    }

    while (currentDate <= effectiveEndDate) {
      paymentDates.push(new Date(currentDate.getTime()));
      currentDate = addFrequency(currentDate, contract.frequency);
    }

    return paymentDates;
  }

  calculateVendorEvents(
    contracts: VendorContractData[],
    startDate: Date,
    endDate: Date,
    entity?: string,
    paymentOverrides: VendorPaymentOverrideData[] = []
  ): ExpenseEventData[] {
    const events: ExpenseEventData[] = [];

    const overrideLookup = new Map<string, VendorPaymentOverrideData>();
    for (const override of paymentOverrides) {
      const key = `${override.contractId}_${override.originalDate.toISOString().split('T')[0]}`;
      overrideLookup.set(key, override);
    }

    for (const contract of contracts) {
      if (contract.status !== 'Active') continue;
      if (entity && entity !== 'Consolidated' && contract.entity !== entity) continue;
      if (contract.startDate && endDate < contract.startDate) continue;

      const paymentDates = this.getVendorPaymentDates(contract, startDate, endDate);

      for (let paymentDate of paymentDates) {
        if (contract.startDate && paymentDate < contract.startDate) continue;

        const overrideKey = `${contract.id}_${paymentDate.toISOString().split('T')[0]}`;
        const override = overrideLookup.get(overrideKey);

        if (override) {
          if (override.action === 'skip') continue;
          if (override.action === 'move' && override.newDate) {
            paymentDate = override.newDate;
            if (paymentDate < startDate || paymentDate > endDate) continue;
          }
        }

        events.push({
          date: paymentDate,
          vendorId: contract.id,
          vendorName: contract.vendorName,
          amount: contract.amount,
          entity: contract.entity,
          category: contract.category,
          priority: contract.priority,
          isPayroll: false,
        });
      }
    }

    return events;
  }

  calculateExpenseEvents(
    vendorContracts: VendorContractData[],
    startDate: Date,
    endDate: Date,
    entity: string,
    paymentOverrides: VendorPaymentOverrideData[] = []
  ): ExpenseEventData[] {
    const events = this.calculateVendorEvents(
      vendorContracts, startDate, endDate, entity, paymentOverrides
    );

    events.sort((a, b) => {
      const dateDiff = a.date.getTime() - b.date.getTime();
      if (dateDiff !== 0) return dateDiff;
      return a.priority - b.priority;
    });

    return events;
  }

  calculateTotalExpensesByPeriod(
    events: ExpenseEventData[],
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
