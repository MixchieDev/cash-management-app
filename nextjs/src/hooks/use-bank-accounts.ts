'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';

export interface BankAccount {
  name: string;
  entity: string;
}

const DEFAULT_ACCOUNTS: BankAccount[] = [
  { name: 'Main Account', entity: 'YAHSHUA' },
  { name: 'Main Account', entity: 'ABBA' },
];

export function useBankAccounts(): BankAccount[] {
  const setting = useQuery(api.settings.getByKey, { key: 'bank_accounts' });

  if (setting?.settingValue) {
    try {
      const parsed = JSON.parse(setting.settingValue);
      if (Array.isArray(parsed) && parsed.length > 0 && typeof parsed[0] === 'object') {
        return parsed;
      }
    } catch {
      // fall through to defaults
    }
  }

  return DEFAULT_ACCOUNTS;
}

export function useBankAccountsForEntity(entity: string): string[] {
  const all = useBankAccounts();
  return all.filter((a) => a.entity === entity).map((a) => a.name);
}

export { DEFAULT_ACCOUNTS };
