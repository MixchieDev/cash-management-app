'use client';

import { useState } from 'react';
import { formatCurrency } from '@/lib/currency';
import { useBankBalances, useDeleteBankBalance } from '@/hooks/use-contracts';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import { BankBalanceForm } from './bank-balance-form';
import { toast } from 'sonner';
import { Plus, Trash2 } from 'lucide-react';
import type { BankBalance, EntityOrConsolidated } from '@/lib/types';

interface BankBalanceTableProps {
  entity: EntityOrConsolidated;
}

export function BankBalanceTable({ entity }: BankBalanceTableProps) {
  const balances = useBankBalances(entity);
  const deleteMutation = useDeleteBankBalance();
  const [formOpen, setFormOpen] = useState(false);

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync({ id });
      toast.success('Bank balance entry deleted');
    } catch {
      toast.error('Failed to delete bank balance');
    }
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-PH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  if (!balances) {
    return (
      <div className="flex items-center justify-center py-16 text-[#86868B]">
        Loading bank balances...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#86868B]">
            Bank balance snapshots used as starting cash positions for projections.
          </p>
        </div>
        <Button onClick={() => setFormOpen(true)} className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90">
          <Plus className="h-4 w-4" data-icon="inline-start" />
          Add Balance
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-[#E5E5E7] bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-[#E5E5E7] bg-[#F5F5F7]/60">
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Date</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Entity</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold text-right">Balance</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Source</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Notes</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold w-[80px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {balances.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-12 text-[#86868B]">
                  No bank balance snapshots yet. Add one to set starting cash for projections.
                </TableCell>
              </TableRow>
            ) : (
              balances.map((balance: BankBalance) => (
                <TableRow key={balance._id} className="border-[#E5E5E7] hover:bg-[#F5F5F7]/80">
                  <TableCell className="font-medium text-[#1D1D1F]">
                    {formatDate(balance.balanceDate)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={`text-[11px] font-medium px-2 py-0.5 ${
                        balance.entity === 'YAHSHUA'
                          ? 'bg-[#007AFF]/10 text-[#007AFF]'
                          : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                      }`}
                    >
                      {balance.entity}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-semibold text-[#1D1D1F] tabular-nums">
                    {formatCurrency(balance.balance)}
                  </TableCell>
                  <TableCell className="text-[#86868B]">{balance.source}</TableCell>
                  <TableCell className="text-[#86868B] max-w-[200px] truncate">
                    {balance.notes || <span className="text-[#86868B]/40">&mdash;</span>}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => handleDelete(balance._id)}
                      title="Delete"
                    >
                      <Trash2 className="h-3.5 w-3.5 text-[#FF3B30]" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Summary */}
      {balances.length > 0 && (
        <div className="text-xs text-[#86868B] px-1">
          {balances.length} balance snapshot{balances.length !== 1 ? 's' : ''}
        </div>
      )}

      {/* Form Dialog */}
      <BankBalanceForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  );
}
