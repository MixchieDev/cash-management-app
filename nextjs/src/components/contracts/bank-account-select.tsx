'use client';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useBankAccountsForEntity } from '@/hooks/use-bank-accounts';

interface BankAccountSelectProps {
  entity: string;
  value: string;
  onChange: (value: string) => void;
}

export function BankAccountSelect({ entity, value, onChange }: BankAccountSelectProps) {
  const accounts = useBankAccountsForEntity(entity);

  // Include current value if it's not in the list (legacy data)
  const allOptions = [...new Set([...accounts, ...(value && !accounts.includes(value) ? [value] : [])])].sort();

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
        Manage accounts in Settings &gt; Bank Accounts
      </p>
    </div>
  );
}
