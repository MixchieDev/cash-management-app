import { describe, it, expect } from 'vitest';
import { validateAdhocEventInput, isValidISODate } from '../../convex/adhocEventValidation';

const base = {
  eventType: 'inflow',
  date: '2026-07-15',
  amount: 500000,
  description: 'BIR tax refund',
  entity: 'YAHSHUA',
};

describe('validateAdhocEventInput', () => {
  it('accepts a valid inflow', () => {
    expect(validateAdhocEventInput(base)).toEqual({ ok: true });
  });

  it('accepts a valid outflow with category', () => {
    expect(
      validateAdhocEventInput({ ...base, eventType: 'outflow', category: 'Operations' })
    ).toEqual({ ok: true });
  });

  it('rejects unknown eventType', () => {
    expect(validateAdhocEventInput({ ...base, eventType: 'transfer' })).toEqual({
      ok: false,
      error: expect.stringContaining('eventType'),
    });
  });

  it('rejects malformed date', () => {
    expect(validateAdhocEventInput({ ...base, date: '15-07-2026' })).toEqual({
      ok: false,
      error: expect.stringContaining('date'),
    });
  });

  it('rejects zero or negative amount', () => {
    expect(validateAdhocEventInput({ ...base, amount: 0 })).toEqual({
      ok: false,
      error: expect.stringContaining('positive'),
    });
    expect(validateAdhocEventInput({ ...base, amount: -100 })).toEqual({
      ok: false,
      error: expect.stringContaining('positive'),
    });
  });

  it('rejects empty description', () => {
    expect(validateAdhocEventInput({ ...base, description: '   ' })).toEqual({
      ok: false,
      error: expect.stringContaining('description'),
    });
  });

  it('accepts valid confidence levels', () => {
    for (const c of ['committed', 'likely', 'possible']) {
      expect(validateAdhocEventInput({ ...base, confidence: c })).toEqual({ ok: true });
    }
  });

  it('rejects unknown confidence', () => {
    expect(validateAdhocEventInput({ ...base, confidence: 'guess' })).toEqual({
      ok: false,
      error: expect.stringContaining('confidence'),
    });
  });
});

describe('isValidISODate', () => {
  it('accepts ISO dates', () => {
    expect(isValidISODate('2026-01-01')).toBe(true);
  });
  it('rejects impossible dates', () => {
    expect(isValidISODate('2026-02-30')).toBe(false);
  });
});
