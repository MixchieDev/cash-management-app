'use client';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useAccountBalances } from '@/hooks/use-entities';

interface BankAccountSelectProps {
  entity: string;
  value: string;
  onChange: (value: string) => void;
}

export function BankAccountSelect({ entity, value, onChange }: BankAccountSelectProps) {
  const accountData = useAccountBalances() ?? [];

  // Get accounts for the selected entity
  const entityGroup = accountData.find((e: any) => e.entity === entity);
  const accounts = entityGroup?.accounts?.map((a: any) => a.accountName) ?? [];

  // Only show accounts that actually exist in Bank Balances
  const allOptions = [...new Set([...accounts, ...(value && value !== 'Main Account' ? [value] : [])])].filter(Boolean).sort();

  return (
    <div className="space-y-1.5">
      <Label>Bank Account</Label>
      <Select
        value={value}
        onValueChange={(v: string | null) => v && onChange(v)}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select bank account" />
        </SelectTrigger>
        <SelectContent>
          {allOptions.map((name) => (
            <SelectItem key={name} value={name}>
              {name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-[10px] text-slate-400">
        Bank accounts are created in Contracts &gt; Bank Balances
      </p>
    </div>
  );
}
