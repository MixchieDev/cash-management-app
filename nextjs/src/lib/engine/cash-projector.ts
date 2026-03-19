/**
 * Cash projector engine for JESUS Company Cash Management System.
 * Main projection engine that calculates cash flow forecasts.
 *
 * Port of projection_engine/cash_projector.py
 */
import Decimal from 'decimal.js';
import { addDays, addMonths } from 'date-fns';
import { RevenueCalculator, type RevenueEventData, type CustomerContractData, type PaymentOverrideData } from './revenue-calculator';
import { ExpenseScheduler, type ExpenseEventData, type VendorContractData, type VendorPaymentOverrideData } from './expense-scheduler';
import { utcDate, getUTCParts, getDaysInUTCMonth } from './date-utils';

export interface ProjectionDataPointData {
  date: Date;
  startingCash: Decimal;
  inflows: Decimal;
  outflows: Decimal;
  endingCash: Decimal;
  entity: string;
  timeframe: string;
  scenarioType: string;
  isNegative: boolean;
}

export interface ProjectionResultData {
  dataPoints: ProjectionDataPointData[];
  revenueEvents: RevenueEventData[];
  expenseEvents: ExpenseEventData[];
}

export interface ProjectionInput {
  startDate: Date;
  endDate: Date;
  entity: string;
  timeframe?: string;
  scenarioType?: string;
  startingCash: Decimal;
  customerContracts: CustomerContractData[];
  vendorContracts: VendorContractData[];
  customerOverrides?: PaymentOverrideData[];
  vendorOverrides?: VendorPaymentOverrideData[];
  realisticDelayDays?: number;
  /** Events before this date are excluded (assumed already in bank balance). Defaults to startDate. */
  projectionAsOfDate?: Date;
}

export class CashProjector {
  /**
   * Generate list of period-end dates for projection.
   * All dates are UTC to avoid timezone issues.
   */
  generateDateRange(startDate: Date, endDate: Date, timeframe: string = 'monthly'): Date[] {
    const dates: Date[] = [];
    let currentDate = new Date(startDate.getTime());

    if (timeframe === 'daily') {
      while (currentDate <= endDate) {
        dates.push(new Date(currentDate.getTime()));
        currentDate = addDays(currentDate, 1);
      }
    } else if (timeframe === 'weekly') {
      while (currentDate <= endDate) {
        let periodEnd = addDays(currentDate, 6);
        if (periodEnd > endDate) periodEnd = new Date(endDate.getTime());
        dates.push(periodEnd);
        currentDate = addDays(currentDate, 7);
      }
    } else if (timeframe === 'monthly') {
      while (currentDate <= endDate) {
        const { year, month } = getUTCParts(currentDate);
        const lastDay = getDaysInUTCMonth(currentDate);
        let periodEnd = utcDate(year, month, lastDay);
        if (periodEnd > endDate) periodEnd = new Date(endDate.getTime());
        dates.push(periodEnd);
        // Move to first of next month
        currentDate = utcDate(year, month + 1, 1);
      }
    } else if (timeframe === 'quarterly') {
      while (currentDate <= endDate) {
        let periodEnd = addDays(addMonths(currentDate, 3), -1);
        if (periodEnd > endDate) periodEnd = new Date(endDate.getTime());
        dates.push(periodEnd);
        currentDate = addMonths(currentDate, 3);
      }
    } else {
      throw new Error(`Invalid timeframe: ${timeframe}`);
    }

    return dates;
  }

  calculateProjectionDetailed(input: ProjectionInput): ProjectionResultData {
    const {
      startDate,
      endDate,
      entity,
      timeframe = 'monthly',
      scenarioType = 'realistic',
      startingCash,
      customerContracts,
      vendorContracts,
      customerOverrides = [],
      vendorOverrides = [],
      realisticDelayDays,
      projectionAsOfDate,
    } = input;

    const cutoffDate = projectionAsOfDate ?? startDate;

    const revenueCalc = new RevenueCalculator(scenarioType, realisticDelayDays);
    const expenseScheduler = new ExpenseScheduler();

    const allRevenueEvents = revenueCalc.calculateRevenueEvents(
      customerContracts, startDate, endDate, customerOverrides
    );
    const allExpenseEvents = expenseScheduler.calculateExpenseEvents(
      vendorContracts, startDate, endDate, entity, vendorOverrides
    );

    // Filter out past events — they're already reflected in the bank balance
    const revenueEvents = allRevenueEvents.filter((e) => e.date >= cutoffDate);
    const expenseEvents = allExpenseEvents.filter((e) => e.date >= cutoffDate);

    // Collect unique event dates (only days with actual cash movement)
    const eventDateSet = new Set<string>();
    for (const e of revenueEvents) {
      eventDateSet.add(e.date.toISOString().split('T')[0]);
    }
    for (const e of expenseEvents) {
      eventDateSet.add(e.date.toISOString().split('T')[0]);
    }
    const eventDates = Array.from(eventDateSet)
      .sort()
      .map((d) => new Date(d + 'T00:00:00.000Z'));

    // Build data points only on dates with cash movement
    const dataPoints: ProjectionDataPointData[] = [];
    let currentCash = startingCash;

    // For consolidated entity, don't filter by entity name in aggregation
    const entityFilter = entity === 'Consolidated' ? undefined : entity;

    for (const eventDate of eventDates) {
      const inflows = revenueCalc.calculateTotalRevenueByPeriod(
        revenueEvents, eventDate, eventDate, entityFilter
      );
      const outflows = expenseScheduler.calculateTotalExpensesByPeriod(
        expenseEvents, eventDate, eventDate, entityFilter
      );
      const endingCash = currentCash.add(inflows).sub(outflows);

      dataPoints.push({
        date: eventDate,
        startingCash: currentCash,
        inflows,
        outflows,
        endingCash,
        entity,
        timeframe,
        scenarioType,
        isNegative: endingCash.isNegative(),
      });

      currentCash = endingCash;
    }

    return { dataPoints, revenueEvents, expenseEvents };
  }

  calculateProjection(input: ProjectionInput): ProjectionDataPointData[] {
    return this.calculateProjectionDetailed(input).dataPoints;
  }

  getEventsForPeriod(
    result: ProjectionResultData,
    startDate: Date,
    endDate: Date
  ): { revenueEvents: RevenueEventData[]; expenseEvents: ExpenseEventData[] } {
    return {
      revenueEvents: result.revenueEvents.filter(
        (e) => e.date >= startDate && e.date <= endDate
      ),
      expenseEvents: result.expenseEvents.filter(
        (e) => e.date >= startDate && e.date <= endDate
      ),
    };
  }
}
