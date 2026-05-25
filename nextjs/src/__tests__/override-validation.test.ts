import { describe, it, expect } from 'vitest';
import {
  isValidISODate,
  validateOverrideInput,
} from '../../convex/overrideValidation';

const baseMove = {
  overrideType: 'customer',
  contractId: 'abc123',
  originalDate: '2026-03-15',
  newDate: '2026-03-25',
  action: 'move',
  entity: 'YAHSHUA',
};

const baseSkip = {
  overrideType: 'vendor',
  contractId: 'xyz789',
  originalDate: '2026-04-01',
  action: 'skip',
  entity: 'ABBA',
};

describe('isValidISODate', () => {
  it('accepts well-formed dates', () => {
    expect(isValidISODate('2026-01-01')).toBe(true);
    expect(isValidISODate('2026-12-31')).toBe(true);
    expect(isValidISODate('2024-02-29')).toBe(true); // leap year
  });

  it('rejects malformed strings', () => {
    expect(isValidISODate('2026-1-1')).toBe(false);
    expect(isValidISODate('03/15/2026')).toBe(false);
    expect(isValidISODate('2026-03-15T00:00:00Z')).toBe(false);
    expect(isValidISODate('')).toBe(false);
    expect(isValidISODate('not a date')).toBe(false);
  });

  it('rejects impossible dates', () => {
    expect(isValidISODate('2025-02-29')).toBe(false); // not a leap year
    expect(isValidISODate('2026-13-01')).toBe(false); // bad month
    expect(isValidISODate('2026-04-31')).toBe(false); // April has 30
  });
});

describe('validateOverrideInput - happy path', () => {
  it('accepts a valid move override', () => {
    expect(validateOverrideInput(baseMove)).toEqual({ ok: true });
  });

  it('accepts a valid skip override', () => {
    expect(validateOverrideInput(baseSkip)).toEqual({ ok: true });
  });
});

describe('validateOverrideInput - enum checks', () => {
  it('rejects unknown overrideType', () => {
    const result = validateOverrideInput({ ...baseMove, overrideType: 'employee' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('overrideType') });
  });

  it('rejects unknown action', () => {
    const result = validateOverrideInput({ ...baseMove, action: 'delete' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('action') });
  });

  it('rejects empty contractId', () => {
    const result = validateOverrideInput({ ...baseMove, contractId: '   ' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('contractId') });
  });

  it('rejects empty entity', () => {
    const result = validateOverrideInput({ ...baseMove, entity: '' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('entity') });
  });
});

describe('validateOverrideInput - date checks', () => {
  it('rejects malformed originalDate', () => {
    const result = validateOverrideInput({ ...baseMove, originalDate: '15-03-2026' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('originalDate') });
  });

  it('rejects impossible originalDate', () => {
    const result = validateOverrideInput({ ...baseMove, originalDate: '2025-02-30' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('originalDate') });
  });
});

describe('validateOverrideInput - move action rules', () => {
  it('requires newDate when moving', () => {
    const { newDate, ...withoutNewDate } = baseMove;
    void newDate;
    const result = validateOverrideInput(withoutNewDate);
    expect(result).toEqual({ ok: false, error: expect.stringContaining('newDate is required') });
  });

  it('rejects malformed newDate', () => {
    const result = validateOverrideInput({ ...baseMove, newDate: 'tomorrow' });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('newDate') });
  });

  it('rejects same originalDate and newDate (no-op move)', () => {
    const result = validateOverrideInput({
      ...baseMove,
      newDate: baseMove.originalDate,
    });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('differ') });
  });
});

describe('validateOverrideInput - skip action rules', () => {
  it('rejects newDate when skipping', () => {
    const result = validateOverrideInput({
      ...baseSkip,
      newDate: '2026-04-05',
    });
    expect(result).toEqual({ ok: false, error: expect.stringContaining('skip') });
  });
});
