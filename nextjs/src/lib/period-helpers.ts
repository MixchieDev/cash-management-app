/**
 * Helper functions for calculating period ranges from aggregated data points.
 * Port of utils/period_helpers.py
 */
import { format, subDays, subMonths, addDays } from 'date-fns';

export function calculatePeriodRange(
  clickedDate: Date,
  timeframe: string,
  projectionStart: Date
): { periodStart: Date; periodEnd: Date; periodLabel: string } {
  if (timeframe === 'daily') {
    return {
      periodStart: clickedDate,
      periodEnd: clickedDate,
      periodLabel: format(clickedDate, 'MMM dd, yyyy'),
    };
  }

  if (timeframe === 'weekly') {
    const periodEnd = clickedDate;
    let periodStart = subDays(clickedDate, 6);
    if (periodStart < projectionStart) periodStart = projectionStart;

    return {
      periodStart,
      periodEnd,
      periodLabel: `Week of ${format(periodStart, 'MMM dd')}-${format(periodEnd, 'dd, yyyy')}`,
    };
  }

  if (timeframe === 'monthly') {
    const periodEnd = clickedDate;
    const periodStart = new Date(clickedDate.getFullYear(), clickedDate.getMonth(), 1);

    return {
      periodStart,
      periodEnd,
      periodLabel: format(clickedDate, 'MMMM yyyy'),
    };
  }

  if (timeframe === 'quarterly') {
    const periodEnd = clickedDate;
    let periodStart = addDays(subMonths(clickedDate, 3), 1);
    if (periodStart < projectionStart) periodStart = projectionStart;

    const quarter = Math.floor(clickedDate.getMonth() / 3) + 1;

    return {
      periodStart,
      periodEnd,
      periodLabel: `Q${quarter} ${clickedDate.getFullYear()}`,
    };
  }

  throw new Error(`Invalid timeframe: ${timeframe}`);
}

export function getPeriodDescription(periodStart: Date, periodEnd: Date): string {
  if (periodStart.getTime() === periodEnd.getTime()) {
    return format(periodStart, 'MMM dd, yyyy');
  }
  if (periodStart.getMonth() === periodEnd.getMonth()) {
    return `${format(periodStart, 'MMM dd')}-${format(periodEnd, 'dd, yyyy')}`;
  }
  return `${format(periodStart, 'MMM dd')} - ${format(periodEnd, 'MMM dd, yyyy')}`;
}
