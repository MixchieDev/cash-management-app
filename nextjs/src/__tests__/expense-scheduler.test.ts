import { describe, it, expect } from 'vitest';
import Decimal from 'decimal.js';
import { ExpenseScheduler, type VendorContractData } from '../lib/engine/expense-scheduler';
import { utcDate } from '../lib/engine/date-utils';

function makeVendor(overrides: Partial<VendorContractData> = {}): VendorContractData {
  return {
    id: 1,
    vendorName: 'Test Vendor',
    category: 'Software/Tech',
    amount: new Decimal('50000'),
    frequency: 'Monthly',
    dueDate: utcDate(2026, 0, 15),
    startDate: null,
    endDate: null,
    entity: 'YAHSHUA',
    priority: 3,
    flexibilityDays: 7,
    status: 'Active',
    ...overrides,
  };
}

describe('ExpenseScheduler', () => {
  describe('getVendorPaymentDates', () => {
    it('generates monthly payment dates', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor(), utcDate(2026, 0, 1), utcDate(2026, 5, 30)
      );
      expect(dates).toHaveLength(6);
      expect(dates[0].getUTCDate()).toBe(15);
    });

    it('handles one-time payments', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor({ frequency: 'One-time', dueDate: utcDate(2026, 2, 1) }),
        utcDate(2026, 0, 1), utcDate(2026, 11, 31)
      );
      expect(dates).toHaveLength(1);
      expect(dates[0].getUTCMonth()).toBe(2);
    });

    it('respects start_date', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor({ startDate: utcDate(2026, 2, 1) }),
        utcDate(2026, 0, 1), utcDate(2026, 5, 30)
      );
      expect(dates).toHaveLength(4);
    });

    it('respects end_date', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor({ endDate: utcDate(2026, 2, 31) }),
        utcDate(2026, 0, 1), utcDate(2026, 11, 31)
      );
      expect(dates).toHaveLength(3);
    });

    it('returns empty for out-of-range one-time', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor({ frequency: 'One-time', dueDate: utcDate(2025, 5, 1) }),
        utcDate(2026, 0, 1), utcDate(2026, 11, 31)
      );
      expect(dates).toHaveLength(0);
    });

    it('generates quarterly payment dates', () => {
      const scheduler = new ExpenseScheduler();
      const dates = scheduler.getVendorPaymentDates(
        makeVendor({ frequency: 'Quarterly', dueDate: utcDate(2026, 0, 15) }),
        utcDate(2026, 0, 1), utcDate(2026, 11, 31)
      );
      expect(dates).toHaveLength(4);
    });
  });

  describe('calculateExpenseEvents', () => {
    it('filters by entity', () => {
      const scheduler = new ExpenseScheduler();
      const events = scheduler.calculateExpenseEvents(
        [makeVendor({ id: 1, entity: 'YAHSHUA' }), makeVendor({ id: 2, entity: 'ABBA', vendorName: 'ABBA Vendor' })],
        utcDate(2026, 0, 1), utcDate(2026, 0, 31), 'YAHSHUA'
      );
      expect(events.every((e) => e.entity === 'YAHSHUA')).toBe(true);
    });

    it('skips inactive contracts', () => {
      const scheduler = new ExpenseScheduler();
      const events = scheduler.calculateExpenseEvents(
        [makeVendor({ status: 'Active' }), makeVendor({ id: 2, status: 'Inactive' })],
        utcDate(2026, 0, 1), utcDate(2026, 0, 31), 'YAHSHUA'
      );
      expect(events).toHaveLength(1);
    });

    it('sorts by date then priority', () => {
      const scheduler = new ExpenseScheduler();
      const events = scheduler.calculateExpenseEvents(
        [makeVendor({ id: 1, priority: 3, vendorName: 'P3 Vendor' }), makeVendor({ id: 2, priority: 1, vendorName: 'P1 Vendor' })],
        utcDate(2026, 0, 1), utcDate(2026, 0, 31), 'YAHSHUA'
      );
      expect(events[0].vendorName).toBe('P1 Vendor');
      expect(events[1].vendorName).toBe('P3 Vendor');
    });

    it('applies skip override', () => {
      const scheduler = new ExpenseScheduler();
      const events = scheduler.calculateExpenseEvents(
        [makeVendor()],
        utcDate(2026, 0, 1), utcDate(2026, 1, 28), 'YAHSHUA',
        [{ contractId: 1, originalDate: utcDate(2026, 0, 15), newDate: null, action: 'skip' }]
      );
      expect(events).toHaveLength(1);
    });
  });

  describe('calculateTotalExpensesByPeriod', () => {
    it('sums expenses within period', () => {
      const scheduler = new ExpenseScheduler();
      const events = scheduler.calculateExpenseEvents(
        [makeVendor({ amount: new Decimal('50000') })],
        utcDate(2026, 0, 1), utcDate(2026, 2, 31), 'YAHSHUA'
      );
      const total = scheduler.calculateTotalExpensesByPeriod(events, utcDate(2026, 0, 1), utcDate(2026, 0, 31));
      expect(total.equals(new Decimal('50000'))).toBe(true);
    });
  });
});
