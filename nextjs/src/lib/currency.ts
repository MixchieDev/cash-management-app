/**
 * Currency formatting utilities for JESUS Company Cash Management System.
 * ALL currency displays MUST use these functions to ensure consistency.
 * Format: ₱X,XXX.XX (Philippine Peso with comma separators and 2 decimals)
 *
 * Port of utils/currency_formatter.py
 */
import Decimal from 'decimal.js';

const CURRENCY_SYMBOL = '₱';

export function formatCurrency(amount: Decimal | number | string): string {
  const dec = new Decimal(amount).toDecimalPlaces(2);
  const isNegative = dec.isNegative();
  const abs = dec.abs();

  const [integerPart, decimalPart] = abs.toFixed(2).split('.');
  const formattedInteger = parseInt(integerPart).toLocaleString('en-US');

  const formatted = `${CURRENCY_SYMBOL}${formattedInteger}.${decimalPart}`;
  return isNegative ? `-${formatted}` : formatted;
}

export function parseCurrency(formatted: string): Decimal {
  const cleaned = formatted.replace(CURRENCY_SYMBOL, '').replace(/,/g, '').trim();
  return new Decimal(cleaned);
}

export function formatCurrencyCompact(amount: Decimal | number | string): string {
  const dec = new Decimal(amount);
  const isNegative = dec.isNegative();
  const abs = dec.abs();

  let value: Decimal;
  let suffix: string;

  if (abs.gte(1_000_000_000)) {
    value = abs.div(1_000_000_000);
    suffix = 'B';
  } else if (abs.gte(1_000_000)) {
    value = abs.div(1_000_000);
    suffix = 'M';
  } else if (abs.gte(1_000)) {
    value = abs.div(1_000);
    suffix = 'K';
  } else {
    return formatCurrency(dec);
  }

  const formatted = `${CURRENCY_SYMBOL}${value.toFixed(2)}${suffix}`;
  return isNegative ? `-${formatted}` : formatted;
}

export function validateCurrencyFormat(formatted: string): boolean {
  return /^-?₱\d{1,3}(,\d{3})*\.\d{2}$/.test(formatted);
}
