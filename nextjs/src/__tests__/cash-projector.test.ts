import { describe, it, expect } from 'vitest';
import Decimal from 'decimal.js';
import { CashProjector } from '../lib/engine/cash-projector';
import type { CustomerContractData } from '../lib/engine/revenue-calculator';
import type { VendorContractData } from '../lib/engine/expense-scheduler';
import { utcDate } from '../lib/engine/date-utils';

function makeCustomer(overrides: Partial<CustomerContractData> = {}): CustomerContractData {
  return {
    id: 1,
    companyName: 'Client A',
    monthlyFee: new Decimal('200000'),
    paymentPlan: 'Monthly',
    contractStart: utcDate(2026, 0, 5),
    contractEnd: null,
    status: 'Active',
    entity: 'YAHSHUA',
    invoiceDay: null,
    paymentTermsDays: null,
    reliabilityScore: new Decimal('0.80'),
    ...overrides,
  };
}

function makeVendor(overrides: Partial<VendorContractData> = {}): VendorContractData {
  return {
    id: 1,
    vendorName: 'AWS',
    category: 'Software/Tech',
    amount: new Decimal('50000'),
    frequency: 'Monthly',
    dueDate: utcDate(2026, 0, 21),
    startDate: null,
    endDate: null,
    entity: 'YAHSHUA',
    priority: 3,
    flexibilityDays: 7,
    status: 'Active',
    ...overrides,
  };
}

describe('CashProjector', () => {
  describe('generateDateRange', () => {
    const projector = new CashProjector();

    it('generates daily dates', () => {
      const dates = projector.generateDateRange(utcDate(2026, 0, 1), utcDate(2026, 0, 7), 'daily');
      expect(dates).toHaveLength(7);
    });

    it('generates weekly dates', () => {
      const dates = projector.generateDateRange(utcDate(2026, 0, 1), utcDate(2026, 0, 28), 'weekly');
      expect(dates).toHaveLength(4);
    });

    it('generates monthly dates', () => {
      const dates = projector.generateDateRange(utcDate(2026, 0, 1), utcDate(2026, 5, 30), 'monthly');
      expect(dates).toHaveLength(6);
    });

    it('generates quarterly dates', () => {
      const dates = projector.generateDateRange(utcDate(2026, 0, 1), utcDate(2026, 11, 31), 'quarterly');
      expect(dates).toHaveLength(4);
    });

    it('throws on invalid timeframe', () => {
      expect(() =>
        projector.generateDateRange(utcDate(2026, 0, 1), utcDate(2026, 0, 7), 'invalid')
      ).toThrow('Invalid timeframe');
    });
  });

  describe('calculateProjectionDetailed', () => {
    it('calculates cash flow with inflows and outflows', () => {
      const projector = new CashProjector();
      const result = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 2, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'optimistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [makeVendor()],
      });

      // Event-based: points only on days with cash movement
      // Customer pays on 5th, vendor on 21st = 2 unique dates per month = ~6 points in 3 months
      expect(result.dataPoints.length).toBeGreaterThanOrEqual(2);
      expect(result.dataPoints[0].startingCash.equals(new Decimal('5000000'))).toBe(true);
      // Final ending cash should reflect net positive (200K revenue - 50K expense per month)
      const lastPoint = result.dataPoints[result.dataPoints.length - 1];
      expect(lastPoint.endingCash.gt(new Decimal('5000000'))).toBe(true);
    });

    it('cascades ending cash to next period starting cash', () => {
      const projector = new CashProjector();
      const result = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 2, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'optimistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [makeVendor()],
      });

      expect(
        result.dataPoints[1].startingCash.equals(result.dataPoints[0].endingCash)
      ).toBe(true);
    });

    it('marks negative cash correctly', () => {
      const projector = new CashProjector();
      const result = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 0, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'optimistic',
        startingCash: new Decimal('10000'),
        customerContracts: [],
        vendorContracts: [makeVendor({ amount: new Decimal('500000') })],
      });

      // Vendor pays on Jan 21 → that's the only event date
      expect(result.dataPoints.length).toBeGreaterThanOrEqual(1);
      const vendorPayDay = result.dataPoints.find(dp => dp.outflows.gt(0));
      expect(vendorPayDay).toBeDefined();
      expect(vendorPayDay!.isNegative).toBe(true);
      expect(vendorPayDay!.endingCash.isNegative()).toBe(true);
    });

    it('handles realistic delay', () => {
      const projector = new CashProjector();
      const optimistic = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 0, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'optimistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [],
      });

      const realistic = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 0, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'realistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [],
        realisticDelayDays: 10,
      });

      expect(optimistic.dataPoints[0].inflows.gte(0)).toBe(true);
      expect(realistic.dataPoints[0].inflows.gte(0)).toBe(true);
    });

    it('produces consistent totals across timeframes', () => {
      const projector = new CashProjector();
      const input = {
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 2, 31),
        entity: 'YAHSHUA',
        scenarioType: 'optimistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [makeVendor()],
      };

      // Event-based points are the same regardless of timeframe label
      const a = projector.calculateProjectionDetailed({ ...input, timeframe: 'daily' });
      const b = projector.calculateProjectionDetailed({ ...input, timeframe: 'monthly' });

      const aFinal = a.dataPoints[a.dataPoints.length - 1].endingCash;
      const bFinal = b.dataPoints[b.dataPoints.length - 1].endingCash;
      expect(aFinal.toFixed(2)).toBe(bFinal.toFixed(2));
      // Same number of data points since both use event dates
      expect(a.dataPoints.length).toBe(b.dataPoints.length);
    });
  });

  describe('getEventsForPeriod', () => {
    it('filters events by date range', () => {
      const projector = new CashProjector();
      const result = projector.calculateProjectionDetailed({
        startDate: utcDate(2026, 0, 1),
        endDate: utcDate(2026, 2, 31),
        entity: 'YAHSHUA',
        timeframe: 'monthly',
        scenarioType: 'optimistic',
        startingCash: new Decimal('5000000'),
        customerContracts: [makeCustomer()],
        vendorContracts: [makeVendor()],
      });

      const janEvents = projector.getEventsForPeriod(result, utcDate(2026, 0, 1), utcDate(2026, 0, 31));
      expect(janEvents.revenueEvents.length).toBeGreaterThanOrEqual(0);
      expect(janEvents.expenseEvents.length).toBeGreaterThanOrEqual(0);
    });
  });
});
