import { describe, it, expect } from 'vitest';
import { formatCurrency, parseCurrency, formatCurrencyCompact, validateCurrencyFormat } from '../lib/currency';
import Decimal from 'decimal.js';

describe('formatCurrency', () => {
  it('formats basic amounts', () => {
    expect(formatCurrency(2500000)).toBe('₱2,500,000.00');
    expect(formatCurrency(0)).toBe('₱0.00');
    expect(formatCurrency(1234567.89)).toBe('₱1,234,567.89');
  });

  it('formats Decimal values', () => {
    expect(formatCurrency(new Decimal('2500000'))).toBe('₱2,500,000.00');
    expect(formatCurrency(new Decimal('50000.50'))).toBe('₱50,000.50');
  });

  it('formats negative amounts', () => {
    expect(formatCurrency(-150000.50)).toBe('-₱150,000.50');
    expect(formatCurrency(new Decimal('-150000.50'))).toBe('-₱150,000.50');
  });

  it('rounds to 2 decimal places', () => {
    expect(formatCurrency(1234.567)).toBe('₱1,234.57');
    expect(formatCurrency(1234.001)).toBe('₱1,234.00');
  });

  it('formats string amounts', () => {
    expect(formatCurrency('2500000')).toBe('₱2,500,000.00');
  });
});

describe('parseCurrency', () => {
  it('parses formatted currency strings', () => {
    expect(parseCurrency('₱2,500,000.00').equals(new Decimal('2500000.00'))).toBe(true);
    expect(parseCurrency('-₱150,000.50').equals(new Decimal('-150000.50'))).toBe(true);
  });
});

describe('formatCurrencyCompact', () => {
  it('formats in billions', () => {
    expect(formatCurrencyCompact(1500000000)).toBe('₱1.50B');
  });

  it('formats in millions', () => {
    expect(formatCurrencyCompact(2500000)).toBe('₱2.50M');
  });

  it('formats in thousands', () => {
    expect(formatCurrencyCompact(50000)).toBe('₱50.00K');
  });

  it('formats small amounts normally', () => {
    expect(formatCurrencyCompact(500)).toBe('₱500.00');
  });

  it('handles negative compact amounts', () => {
    expect(formatCurrencyCompact(-2500000)).toBe('-₱2.50M');
  });
});

describe('validateCurrencyFormat', () => {
  it('validates correct formats', () => {
    expect(validateCurrencyFormat('₱2,500,000.00')).toBe(true);
    expect(validateCurrencyFormat('₱0.00')).toBe(true);
    expect(validateCurrencyFormat('-₱150,000.50')).toBe(true);
  });

  it('rejects incorrect formats', () => {
    expect(validateCurrencyFormat('2500000')).toBe(false);
    expect(validateCurrencyFormat('₱2,500,000')).toBe(false);
    expect(validateCurrencyFormat('₱2500000.00')).toBe(false);
  });
});
