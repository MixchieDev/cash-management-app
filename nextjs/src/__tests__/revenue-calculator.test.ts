import { describe, it, expect } from 'vitest';
import Decimal from 'decimal.js';
import { RevenueCalculator, type CustomerContractData } from '../lib/engine/revenue-calculator';
import { utcDate } from '../lib/engine/date-utils';

function makeContract(overrides: Partial<CustomerContractData> = {}): CustomerContractData {
  return {
    id: 1,
    companyName: 'Test Corp',
    monthlyFee: new Decimal('100000'),
    paymentPlan: 'Monthly',
    contractStart: utcDate(2026, 0, 5), // Jan 5, 2026
    contractEnd: null,
    status: 'Active',
    entity: 'YAHSHUA',
    invoiceDay: null,
    paymentTermsDays: null,
    reliabilityScore: new Decimal('0.80'),
    ...overrides,
  };
}

describe('RevenueCalculator', () => {
  describe('calculatePaymentDate', () => {
    it('uses contract start day for payment date', () => {
      const calc = new RevenueCalculator('optimistic');
      const billingMonth = utcDate(2026, 3, 1); // April 2026
      const contractStart = utcDate(2026, 0, 5); // Jan 5

      const result = calc.calculatePaymentDate(billingMonth, contractStart);
      expect(result.getUTCFullYear()).toBe(2026);
      expect(result.getUTCMonth()).toBe(3); // April
      expect(result.getUTCDate()).toBe(5);
    });

    it('adds realistic delay', () => {
      const calc = new RevenueCalculator('realistic', 10);
      const billingMonth = utcDate(2026, 3, 1);
      const contractStart = utcDate(2026, 0, 5);

      const result = calc.calculatePaymentDate(billingMonth, contractStart);
      expect(result.getUTCDate()).toBe(15); // 5 + 10 = 15
    });

    it('uses invoice_day override when set', () => {
      const calc = new RevenueCalculator('optimistic');
      const billingMonth = utcDate(2026, 3, 1);
      const contractStart = utcDate(2026, 0, 5);

      const result = calc.calculatePaymentDate(billingMonth, contractStart, 20);
      expect(result.getUTCDate()).toBe(20);
    });

    it('caps day at month max (February)', () => {
      const calc = new RevenueCalculator('optimistic');
      const billingMonth = utcDate(2026, 1, 1); // Feb 2026 (28 days)
      const contractStart = utcDate(2026, 0, 31);

      const result = calc.calculatePaymentDate(billingMonth, contractStart);
      expect(result.getUTCDate()).toBe(28);
    });
  });

  describe('getBillingMonths', () => {
    it('generates monthly billing months', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Monthly',
        contractStart: utcDate(2026, 0, 1),
      });

      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 0, 1),
        utcDate(2026, 5, 30) // 6 months
      );

      expect(months).toHaveLength(6);
    });

    it('generates quarterly billing months', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Quarterly',
        contractStart: utcDate(2026, 0, 1),
      });

      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 0, 1),
        utcDate(2026, 11, 31)
      );

      expect(months).toHaveLength(4);
    });

    it('respects contract end date', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        contractStart: utcDate(2026, 0, 1),
        contractEnd: utcDate(2026, 2, 31),
      });

      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 0, 1),
        utcDate(2026, 11, 31)
      );

      expect(months).toHaveLength(3);
    });

    // Regression: when the projection starts mid-cycle, the engine used to
    // snap currentMonth to the projection-start month, which invented
    // phantom billing months and skipped the real next-due payment.
    // It must keep the contract's natural cadence — see Del Monte
    // Philippines case (Quarterly, Mar start, projection from late May).
    it('keeps the natural quarterly cadence when projection starts mid-cycle', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Quarterly',
        contractStart: utcDate(2026, 2, 1), // Mar 1, 2026
      });

      // Projection window: May 25, 2026 → Dec 31, 2026 (matches a daily
      // dashboard view ~7 months out from a late-May balance date).
      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 4, 25),
        utcDate(2026, 11, 31)
      );

      // Expect Jun/Sep/Dec — NOT May (which is off-cycle).
      expect(months.map((d) => d.toISOString().slice(0, 10))).toEqual([
        '2026-06-01',
        '2026-09-01',
        '2026-12-01',
      ]);
    });

    it('keeps the natural annual cadence when projection starts mid-year', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Annual',
        contractStart: utcDate(2025, 0, 5), // Jan 5, 2025
      });

      // Projection window: May 25, 2026 → May 25, 2027.
      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 4, 25),
        utcDate(2027, 4, 25)
      );

      // Real anniversary is January — not May.
      expect(months.map((d) => d.toISOString().slice(0, 10))).toEqual([
        '2027-01-01',
      ]);
    });

    it('keeps the natural bi-annual cadence when projection starts off-cycle', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Bi-annually',
        contractStart: utcDate(2025, 1, 1), // Feb 1, 2025
      });

      // Cycle is Feb/Aug. Projection from May 25, 2026.
      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 4, 25),
        utcDate(2027, 11, 31)
      );

      expect(months.map((d) => d.toISOString().slice(0, 10))).toEqual([
        '2026-08-01',
        '2027-02-01',
        '2027-08-01',
      ]);
    });

    it('starts at contractStart when projection begins before it', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Quarterly',
        contractStart: utcDate(2026, 5, 1), // Jun 1, 2026 (future)
      });

      const months = calc.getBillingMonths(
        contract,
        utcDate(2026, 0, 1),
        utcDate(2026, 11, 31)
      );

      // Don't bill before the contract starts.
      expect(months.map((d) => d.toISOString().slice(0, 10))).toEqual([
        '2026-06-01',
        '2026-09-01',
        '2026-12-01',
      ]);
    });
  });

  describe('calculateRevenueEvents', () => {
    it('generates events for active contracts only', () => {
      const calc = new RevenueCalculator('optimistic');
      const contracts = [
        makeContract({ id: 1, status: 'Active' }),
        makeContract({ id: 2, status: 'Inactive', companyName: 'Inactive Corp' }),
      ];

      const events = calc.calculateRevenueEvents(
        contracts,
        utcDate(2026, 0, 1),
        utcDate(2026, 2, 31)
      );

      expect(events.every((e) => e.companyName === 'Test Corp')).toBe(true);
    });

    it('calculates quarterly payment amount correctly', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        paymentPlan: 'Quarterly',
        monthlyFee: new Decimal('100000'),
        contractStart: utcDate(2026, 0, 1),
      });

      const events = calc.calculateRevenueEvents(
        [contract],
        utcDate(2026, 0, 1),
        utcDate(2026, 2, 31)
      );

      expect(events).toHaveLength(1);
      expect(events[0].amount.equals(new Decimal('300000'))).toBe(true);
    });

    it('skips overridden payments', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({ contractStart: utcDate(2026, 0, 5) });

      const events = calc.calculateRevenueEvents(
        [contract],
        utcDate(2026, 0, 1),
        utcDate(2026, 2, 31),
        [{ contractId: 1, originalDate: utcDate(2026, 0, 5), newDate: null, action: 'skip' }]
      );

      expect(events).toHaveLength(2);
    });

    it('moves overridden payments to new date', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({ contractStart: utcDate(2026, 0, 5) });

      const events = calc.calculateRevenueEvents(
        [contract],
        utcDate(2026, 0, 1),
        utcDate(2026, 2, 31),
        [{ contractId: 1, originalDate: utcDate(2026, 0, 5), newDate: utcDate(2026, 0, 25), action: 'move' }]
      );

      const janEvent = events.find((e) => e.date.getUTCMonth() === 0);
      expect(janEvent?.date.getUTCDate()).toBe(25);
    });
  });

  describe('calculateTotalRevenueByPeriod', () => {
    it('sums revenue within period', () => {
      const calc = new RevenueCalculator('optimistic');
      const contract = makeContract({
        contractStart: utcDate(2026, 0, 5),
        monthlyFee: new Decimal('100000'),
      });

      const events = calc.calculateRevenueEvents(
        [contract],
        utcDate(2026, 0, 1),
        utcDate(2026, 2, 31)
      );

      const total = calc.calculateTotalRevenueByPeriod(
        events,
        utcDate(2026, 0, 1),
        utcDate(2026, 0, 31)
      );

      expect(total.equals(new Decimal('100000'))).toBe(true);
    });

    it('filters by entity', () => {
      const calc = new RevenueCalculator('optimistic');
      const contracts = [
        makeContract({ id: 1, entity: 'YAHSHUA', contractStart: utcDate(2026, 0, 5) }),
        makeContract({ id: 2, entity: 'ABBA', companyName: 'ABBA Client', contractStart: utcDate(2026, 0, 5) }),
      ];

      const events = calc.calculateRevenueEvents(
        contracts,
        utcDate(2026, 0, 1),
        utcDate(2026, 0, 31)
      );

      const yahshuaTotal = calc.calculateTotalRevenueByPeriod(
        events,
        utcDate(2026, 0, 1),
        utcDate(2026, 0, 31),
        'YAHSHUA'
      );

      expect(yahshuaTotal.equals(new Decimal('100000'))).toBe(true);
    });
  });
});
