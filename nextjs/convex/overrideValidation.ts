/**
 * Pure validation for payment override input.
 * Kept Convex-runtime-free so it can be unit tested.
 */

export type OverrideInput = {
  overrideType: string;
  contractId: string;
  originalDate: string;
  newDate?: string;
  action: string;
  entity: string;
  reason?: string;
};

export type ValidationResult =
  | { ok: true }
  | { ok: false; error: string };

const OVERRIDE_TYPES = ['customer', 'vendor'] as const;
const ACTIONS = ['move', 'skip'] as const;
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

export function validateOverrideInput(input: OverrideInput): ValidationResult {
  if (!OVERRIDE_TYPES.includes(input.overrideType as typeof OVERRIDE_TYPES[number])) {
    return { ok: false, error: `overrideType must be one of: ${OVERRIDE_TYPES.join(', ')}` };
  }
  if (!ACTIONS.includes(input.action as typeof ACTIONS[number])) {
    return { ok: false, error: `action must be one of: ${ACTIONS.join(', ')}` };
  }
  if (!input.contractId || input.contractId.trim().length === 0) {
    return { ok: false, error: 'contractId is required' };
  }
  if (!input.entity || input.entity.trim().length === 0) {
    return { ok: false, error: 'entity is required' };
  }
  if (!isValidISODate(input.originalDate)) {
    return { ok: false, error: 'originalDate must be a valid date in YYYY-MM-DD format' };
  }
  if (input.action === 'move') {
    if (!input.newDate) {
      return { ok: false, error: 'newDate is required when action is "move"' };
    }
    if (!isValidISODate(input.newDate)) {
      return { ok: false, error: 'newDate must be a valid date in YYYY-MM-DD format' };
    }
    if (input.newDate === input.originalDate) {
      return { ok: false, error: 'newDate must differ from originalDate for a move action' };
    }
  }
  if (input.action === 'skip' && input.newDate) {
    return { ok: false, error: 'newDate must not be provided when action is "skip"' };
  }
  return { ok: true };
}
