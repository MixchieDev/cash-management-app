import { describe, it, expect } from 'vitest';
import Decimal from 'decimal.js';
import { ScenarioCalculator, type ScenarioChangeData } from '../lib/engine/scenario-calculator';
import type { ProjectionDataPointData } from '../lib/engine/cash-projector';

function makeBaseline(): ProjectionDataPointData[] {
  return [
    {
      date: new Date(2026, 0, 31),
      startingCash: new Decimal('5000000'),
      inflows: new Decimal('200000'),
      outflows: new Decimal('100000'),
      endingCash: new Decimal('5100000'),
      entity: 'YAHSHUA',
      timeframe: 'monthly',
      scenarioType: 'realistic',
      isNegative: false,
    },
    {
      date: new Date(2026, 1, 28),
      startingCash: new Decimal('5100000'),
      inflows: new Decimal('200000'),
      outflows: new Decimal('100000'),
      endingCash: new Decimal('5200000'),
      entity: 'YAHSHUA',
      timeframe: 'monthly',
      scenarioType: 'realistic',
      isNegative: false,
    },
    {
      date: new Date(2026, 2, 31),
      startingCash: new Decimal('5200000'),
      inflows: new Decimal('200000'),
      outflows: new Decimal('100000'),
      endingCash: new Decimal('5300000'),
      entity: 'YAHSHUA',
      timeframe: 'monthly',
      scenarioType: 'realistic',
      isNegative: false,
    },
  ];
}

describe('ScenarioCalculator', () => {
  const calc = new ScenarioCalculator();

  describe('applyScenarioChanges - hiring', () => {
    it('adds payroll to outflows from start date', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'hiring',
          startDate: new Date(2026, 1, 1), // Start Feb
          endDate: null,
          employees: 5,
          salaryPerEmployee: new Decimal('50000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      // Jan: no change (before start_date)
      expect(result[0].outflows.equals(new Decimal('100000'))).toBe(true);

      // Feb: +250K payroll (5 × 50K)
      expect(result[1].outflows.equals(new Decimal('350000'))).toBe(true);

      // Mar: +250K payroll
      expect(result[2].outflows.equals(new Decimal('350000'))).toBe(true);
    });
  });

  describe('applyScenarioChanges - expense', () => {
    it('adds recurring expense to outflows', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'expense',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          expenseAmount: new Decimal('30000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      expect(result[0].outflows.equals(new Decimal('130000'))).toBe(true);
    });
  });

  describe('applyScenarioChanges - revenue', () => {
    it('adds new client revenue to inflows', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'revenue',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          newClients: 3,
          revenuePerClient: new Decimal('100000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      // +300K revenue (3 × 100K)
      expect(result[0].inflows.equals(new Decimal('500000'))).toBe(true);
    });
  });

  describe('applyScenarioChanges - customer_loss', () => {
    it('subtracts lost revenue from inflows', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'customer_loss',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          lostRevenue: new Decimal('50000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      expect(result[0].inflows.equals(new Decimal('150000'))).toBe(true);
    });

    it('does not let inflows go negative', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'customer_loss',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          lostRevenue: new Decimal('500000'), // More than total inflows
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      expect(result[0].inflows.equals(new Decimal('0'))).toBe(true);
    });
  });

  describe('applyScenarioChanges - investment', () => {
    it('adds one-time outflow on exact date', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'investment',
          startDate: new Date(2026, 0, 31), // Exact match on Jan period end
          endDate: null,
          investmentAmount: new Decimal('1000000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      expect(result[0].outflows.equals(new Decimal('1100000'))).toBe(true);
      // Feb and Mar should not be affected (before recalculation of ending cash)
    });
  });

  describe('recalculateEndingCash', () => {
    it('cascades ending cash correctly', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'hiring',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          employees: 10,
          salaryPerEmployee: new Decimal('50000'),
        },
      ];

      const result = calc.applyScenarioChanges(baseline, changes);

      // Verify cascading: each period's starting cash = previous ending cash
      expect(result[1].startingCash.equals(result[0].endingCash)).toBe(true);
      expect(result[2].startingCash.equals(result[1].endingCash)).toBe(true);
    });
  });

  describe('calculateImpactSummary', () => {
    it('calculates differences correctly', () => {
      const baseline = makeBaseline();
      const changes: ScenarioChangeData[] = [
        {
          changeType: 'expense',
          startDate: new Date(2026, 0, 1),
          endDate: null,
          expenseAmount: new Decimal('50000'),
        },
      ];

      const scenario = calc.applyScenarioChanges(baseline, changes);
      const summary = calc.calculateImpactSummary(baseline, scenario);

      // Total outflows increased by 50K × 3 months = 150K
      expect(summary.difference.outflows.equals(new Decimal('150000'))).toBe(true);

      // Ending cash decreased
      expect(summary.difference.endingCash.isNegative()).toBe(true);
    });
  });
});
