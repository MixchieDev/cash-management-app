'use client';

import { useState } from 'react';
import { useAppStore, type SelectedAccount } from '@/stores/app-store';
import { useAccountBalances } from '@/hooks/use-entities';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { formatCurrency } from '@/lib/currency';
import { ChevronDown, Layers } from 'lucide-react';

interface EntityGroup {
  entity: string;
  fullName: string;
  color: string;
  accounts: { accountName: string; balance: number; balanceDate: string }[];
}

export function AccountSelector() {
  const [open, setOpen] = useState(false);
  const {
    selectedAccounts,
    allAccountsSelected,
    setAllAccountsSelected,
    toggleAccount,
  } = useAppStore();

  const accountData = useAccountBalances() as EntityGroup[] | undefined;

  // Calculate total selected balance
  const selectedTotal = allAccountsSelected
    ? (accountData ?? []).reduce(
        (sum, e) => sum + e.accounts.reduce((s, a) => s + a.balance, 0),
        0
      )
    : selectedAccounts.reduce((sum, sel) => {
        const entity = (accountData ?? []).find((e) => e.entity === sel.entity);
        const account = entity?.accounts.find((a) => a.accountName === sel.accountName);
        return sum + (account?.balance ?? 0);
      }, 0);

  const totalAccounts = (accountData ?? []).reduce((sum, e) => sum + e.accounts.length, 0);
  const selectedCount = allAccountsSelected ? totalAccounts : selectedAccounts.length;

  function isAccountSelected(entity: string, accountName: string): boolean {
    if (allAccountsSelected) return true;
    return selectedAccounts.some(
      (a) => a.entity === entity && a.accountName === accountName
    );
  }

  function handleToggleAccount(entity: string, accountName: string) {
    if (allAccountsSelected) {
      // Switch from consolidated to specific — select all EXCEPT this one
      const allAccounts: SelectedAccount[] = [];
      for (const e of accountData ?? []) {
        for (const a of e.accounts) {
          if (!(e.entity === entity && a.accountName === accountName)) {
            allAccounts.push({ entity: e.entity, accountName: a.accountName });
          }
        }
      }
      useAppStore.getState().setSelectedAccounts(allAccounts);
    } else {
      toggleAccount({ entity, accountName });
    }
  }

  const label = allAccountsSelected
    ? 'All Accounts'
    : selectedCount === 0
      ? 'Select accounts'
      : `${selectedCount} account${selectedCount !== 1 ? 's' : ''}`;

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        className="h-9 px-3 text-[13px] bg-white border-slate-200 shadow-sm gap-2"
        onClick={() => setOpen(!open)}
      >
        <Layers className="h-3.5 w-3.5 text-slate-400" />
        <span className="text-slate-700">{label}</span>
        {selectedCount > 0 && (
          <span className="text-[10px] text-slate-400 font-medium tabular-nums">
            {formatCurrency(selectedTotal)}
          </span>
        )}
        <ChevronDown className="h-3 w-3 text-slate-400" />
      </Button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-2 z-50 w-[340px] rounded-xl bg-white border border-slate-200 shadow-xl p-3 space-y-3">
            {/* Consolidated toggle */}
            <div
              className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-slate-50 cursor-pointer"
              onClick={() => {
                setAllAccountsSelected(true);
                setOpen(false);
              }}
            >
              <Checkbox checked={allAccountsSelected} onCheckedChange={() => setAllAccountsSelected(true)} />
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">Consolidated</p>
                <p className="text-[10px] text-slate-400">All entities, all accounts</p>
              </div>
              <span className="text-xs font-medium text-slate-500 tabular-nums">
                {formatCurrency(
                  (accountData ?? []).reduce(
                    (sum, e) => sum + e.accounts.reduce((s, a) => s + a.balance, 0),
                    0
                  )
                )}
              </span>
            </div>

            <div className="border-t border-slate-100" />

            {/* Entity groups */}
            {!accountData ? (
              <p className="text-center text-xs text-slate-400 py-4">Loading accounts...</p>
            ) : accountData.length === 0 ? (
              <p className="text-center text-xs text-slate-400 py-4">No entities configured</p>
            ) : (
              accountData.map((entityGroup) => (
                <div key={entityGroup.entity}>
                  <div className="flex items-center gap-2 px-3 py-1">
                    <span
                      className="h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: entityGroup.color }}
                    />
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      {entityGroup.entity}
                    </span>
                  </div>
                  {entityGroup.accounts.length === 0 ? (
                    <p className="text-xs text-slate-300 px-3 py-1">No bank accounts</p>
                  ) : (
                    entityGroup.accounts.map((account) => (
                      <div
                        key={`${entityGroup.entity}-${account.accountName}`}
                        className="flex items-center gap-3 rounded-lg px-3 py-1.5 hover:bg-slate-50 cursor-pointer"
                        onClick={() => handleToggleAccount(entityGroup.entity, account.accountName)}
                      >
                        <Checkbox
                          checked={isAccountSelected(entityGroup.entity, account.accountName)}
                          onCheckedChange={() => handleToggleAccount(entityGroup.entity, account.accountName)}
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium text-slate-700 truncate">{account.accountName}</p>
                          <p className="text-[10px] text-slate-400">as of {account.balanceDate}</p>
                        </div>
                        <span className="text-xs font-medium text-slate-600 tabular-nums">
                          {formatCurrency(account.balance)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              ))
            )}

            {/* Footer */}
            <div className="border-t border-slate-100 pt-2 flex items-center justify-between px-2">
              <span className="text-[10px] text-slate-400">
                {selectedCount} of {totalAccounts} accounts
              </span>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-blue-600 h-7"
                onClick={() => setOpen(false)}
              >
                Done
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
