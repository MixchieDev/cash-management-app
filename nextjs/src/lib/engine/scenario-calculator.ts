/**
 * Scenario calculator for JESUS Company Cash Management System.
 * Applies scenario changes to baseline projections for what-if analysis.
 *
 * Port of scenario_engine/scenario_calculator.py
 */
import Decimal from 'decimal.js';
import type { ProjectionDataPointData } from './cash-projector';

export interface ScenarioChangeData {
  changeType: string;
  startDate: Date;
  endDate: Date | null;
  // Hiring
  employees?: number;
  salaryPerEmployee?: Decimal;
  // Expense
  expenseName?: string;
  expenseAmount?: Decimal;
  expenseFrequency?: string;
  // Revenue
  newClients?: number;
  revenuePerClient?: Decimal;
  // Investment
  investmentAmount?: Decimal;
  // Customer loss
  lostRevenue?: Decimal;
}

function deepCopyProjection(projection: ProjectionDataPointData[]): ProjectionDataPointData[] {
  return projection.map((p) => ({
    ...p,
    startingCash: new Decimal(p.startingCash),
    inflows: new Decimal(p.inflows),
    outflows: new Decimal(p.outflows),
    endingCash: new Decimal(p.endingCash),
  }));
}

export class ScenarioCalculator {
  /**
   * Apply scenario changes to baseline projection.
   */
  applyScenarioChanges(
    baselineProjection: ProjectionDataPointData[],
    changes: ScenarioChangeData[]
  ): ProjectionDataPointData[] {
    const projection = deepCopyProjection(baselineProjection);

    for (const change of changes) {
      switch (change.changeType) {
        case 'hiring':
          this.applyHiringChange(projection, change);
          break;
        case 'expense':
          this.applyExpenseChange(projection, change);
          break;
        case 'revenue':
          this.applyRevenueChange(projection, change);
          break;
        case 'customer_loss':
          this.applyCustomerLossChange(projection, change);
          break;
        case 'investment':
          this.applyInvestmentChange(projection, change);
          break;
      }
    }

    this.recalculateEndingCash(projection);
    return projection;
  }

  /**
   * Apply multiple scenarios (stacking their changes).
   */
  applyMultipleScenarios(
    baselineProjection: ProjectionDataPointData[],
    scenarioChangesList: ScenarioChangeData[][]
  ): ProjectionDataPointData[] {
    const allChanges = scenarioChangesList.flat();
    return this.applyScenarioChanges(baselineProjection, allChanges);
  }

  private applyHiringChange(projection: ProjectionDataPointData[], change: ScenarioChangeData): void {
    if (!change.employees || !change.salaryPerEmployee) return;
    const additionalPayroll = change.salaryPerEmployee.mul(change.employees);

    for (const point of projection) {
      if (point.date >= change.startDate) {
        if (!change.endDate || point.date <= change.endDate) {
          point.outflows = point.outflows.add(additionalPayroll);
        }
      }
    }
  }

  private applyExpenseChange(projection: ProjectionDataPointData[], change: ScenarioChangeData): void {
    if (!change.expenseAmount) return;

    for (const point of projection) {
      if (point.date >= change.startDate) {
        if (!change.endDate || point.date <= change.endDate) {
          point.outflows = point.outflows.add(change.expenseAmount);
        }
      }
    }
  }

  private applyRevenueChange(projection: ProjectionDataPointData[], change: ScenarioChangeData): void {
    if (!change.newClients || !change.revenuePerClient) return;
    const additionalRevenue = change.revenuePerClient.mul(change.newClients);

    for (const point of projection) {
      if (point.date >= change.startDate) {
        if (!change.endDate || point.date <= change.endDate) {
          point.inflows = point.inflows.add(additionalRevenue);
        }
      }
    }
  }

  private applyCustomerLossChange(projection: ProjectionDataPointData[], change: ScenarioChangeData): void {
    if (!change.lostRevenue) return;

    for (const point of projection) {
      if (point.date >= change.startDate) {
        if (!change.endDate || point.date <= change.endDate) {
          point.inflows = point.inflows.sub(change.lostRevenue);
          if (point.inflows.isNegative()) {
            point.inflows = new Decimal(0);
          }
        }
      }
    }
  }

  private applyInvestmentChange(projection: ProjectionDataPointData[], change: ScenarioChangeData): void {
    if (!change.investmentAmount) return;

    for (const point of projection) {
      if (point.date.getTime() === change.startDate.getTime()) {
        point.outflows = point.outflows.add(change.investmentAmount);
        break;
      }
    }
  }

  /**
   * Recalculate ending cash for all periods after applying changes.
   */
  recalculateEndingCash(projection: ProjectionDataPointData[]): void {
    for (let i = 0; i < projection.length; i++) {
      const point = projection[i];
      if (i === 0) {
        point.endingCash = point.startingCash.add(point.inflows).sub(point.outflows);
      } else {
        point.startingCash = projection[i - 1].endingCash;
        point.endingCash = point.startingCash.add(point.inflows).sub(point.outflows);
      }
      point.isNegative = point.endingCash.isNegative();
    }
  }

  /**
   * Calculate impact summary comparing baseline to scenario.
   */
  calculateImpactSummary(
    baseline: ProjectionDataPointData[],
    scenario: ProjectionDataPointData[]
  ): {
    baseline: { totalInflows: Decimal; totalOutflows: Decimal; endingCash: Decimal };
    scenario: { totalInflows: Decimal; totalOutflows: Decimal; endingCash: Decimal };
    difference: { inflows: Decimal; outflows: Decimal; endingCash: Decimal };
  } {
    const sumInflows = (pts: ProjectionDataPointData[]) =>
      pts.reduce((acc, p) => acc.add(p.inflows), new Decimal(0));
    const sumOutflows = (pts: ProjectionDataPointData[]) =>
      pts.reduce((acc, p) => acc.add(p.outflows), new Decimal(0));

    const baseInflows = sumInflows(baseline);
    const baseOutflows = sumOutflows(baseline);
    const baseEnding = baseline[baseline.length - 1].endingCash;

    const scenInflows = sumInflows(scenario);
    const scenOutflows = sumOutflows(scenario);
    const scenEnding = scenario[scenario.length - 1].endingCash;

    return {
      baseline: { totalInflows: baseInflows, totalOutflows: baseOutflows, endingCash: baseEnding },
      scenario: { totalInflows: scenInflows, totalOutflows: scenOutflows, endingCash: scenEnding },
      difference: {
        inflows: scenInflows.sub(baseInflows),
        outflows: scenOutflows.sub(baseOutflows),
        endingCash: scenEnding.sub(baseEnding),
      },
    };
  }
}
