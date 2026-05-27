/**
 * Pure validation for ad-hoc projection event input.
 * Kept Convex-runtime-free so it can be unit tested.
 */

export type AdhocEventInput = {
  eventType: string;
  date: string;
  amount: number;
  description: string;
  category?: string;
  entity: string;
  bankAccount?: string;
  confidence?: string;
  notes?: string;
};

export type ValidationResult =
  | { ok: true }
  | { ok: false; error: string };

const EVENT_TYPES = ['inflow', 'outflow'] as const;
const CONFIDENCE_LEVELS = ['committed', 'likely', 'possible'] as const;
const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/;

export function isValidISODate(value: string): boolean {
  if (!ISO_DATE.test(value)) return false;
  const [y, m, d] = value.split('-').map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  return (
    date.getUTCFullYear() === y &&
    date.getUTCMonth() === m - 1 &&
    date.getUTCDate() === d
  );
}

export function validateAdhocEventInput(input: AdhocEventInput): ValidationResult {
  if (!EVENT_TYPES.includes(input.eventType as typeof EVENT_TYPES[number])) {
    return { ok: false, error: `eventType must be one of: ${EVENT_TYPES.join(', ')}` };
  }
  if (!isValidISODate(input.date)) {
    return { ok: false, error: 'date must be a valid date in YYYY-MM-DD format' };
  }
  if (typeof input.amount !== 'number' || !Number.isFinite(input.amount)) {
    return { ok: false, error: 'amount must be a finite number' };
  }
  if (input.amount <= 0) {
    return { ok: false, error: 'amount must be positive (eventType decides direction)' };
  }
  if (!input.description || input.description.trim().length === 0) {
    return { ok: false, error: 'description is required' };
  }
  if (!input.entity || input.entity.trim().length === 0) {
    return { ok: false, error: 'entity is required' };
  }
  if (
    input.confidence !== undefined &&
    !CONFIDENCE_LEVELS.includes(input.confidence as typeof CONFIDENCE_LEVELS[number])
  ) {
    return { ok: false, error: `confidence must be one of: ${CONFIDENCE_LEVELS.join(', ')}` };
  }
  return { ok: true };
}
