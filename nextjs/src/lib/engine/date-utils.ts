/**
 * UTC date utilities for the financial engine.
 *
 * JavaScript's Date has a timezone trap:
 *   new Date("2026-03-15")      → March 15 00:00 UTC
 *   new Date(2026, 2, 15)       → March 15 00:00 LOCAL TIME
 *
 * When comparing dates across these two styles, events get missed
 * in daily views because a local-time date can be ±1 day from UTC.
 *
 * Solution: ALL dates in the engine use UTC via this helper.
 */

/**
 * Create a UTC date with no time component.
 * Always use this instead of `new Date(year, month, day)`.
 */
export function utcDate(year: number, month: number, day: number): Date {
  return new Date(Date.UTC(year, month, day));
}

/**
 * Parse an ISO date string to a UTC date.
 * Handles "2026-03-15", "2026-03-15T00:00:00.000Z", and bare day numbers ("15").
 * Bare day numbers are anchored to the current month (for legacy vendor dueDate values).
 */
export function parseDate(dateStr: string): Date {
  const trimmed = dateStr.trim();
  // Handle bare day number (e.g. "15" from old vendor dueDate entries)
  if (/^\d{1,2}$/.test(trimmed)) {
    const now = new Date();
    return utcDate(now.getUTCFullYear(), now.getUTCMonth(), Math.min(parseInt(trimmed, 10), 28));
  }
  const [y, m, d] = trimmed.split('T')[0].split('-').map(Number);
  return utcDate(y, m - 1, d);
}

/**
 * Normalize any Date to UTC midnight (strips time & timezone).
 */
export function normalizeDate(date: Date): Date {
  return utcDate(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate());
}

/**
 * Get UTC year/month/day from a date.
 */
export function getUTCParts(date: Date): { year: number; month: number; day: number } {
  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth(),
    day: date.getUTCDate(),
  };
}

/**
 * Get days in a UTC month.
 */
export function getDaysInUTCMonth(date: Date): number {
  const { year, month } = getUTCParts(date);
  // Day 0 of next month = last day of current month
  return new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
}

/**
 * Format a date as YYYY-MM-DD.
 */
export function formatDateISO(date: Date): string {
  const { year, month, day } = getUTCParts(date);
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}
