'use client';

import { useState, useMemo } from 'react';
import { formatCurrency } from '@/lib/currency';
import { PAYMENT_PLAN_FREQUENCIES } from '@/lib/constants';
import { useCustomers, useDeactivateCustomer, useDeleteCustomer } from '@/hooks/use-contracts';
import { Input } from '@/components/ui/input';
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
import { CustomerForm } from './customer-form';
import { toast } from 'sonner';
import { Checkbox } from '@/components/ui/checkbox';
import { Search, Plus, Pencil, XCircle, Trash2, AlertTriangle } from 'lucide-react';
import type { CustomerContract, EntityOrConsolidated } from '@/lib/types';
import { useEntities, useAccountBalances } from '@/hooks/use-entities';
import Link from 'next/link';

interface CustomerTableProps {
  entity: string;
  accountFilter?: string[];
}

export function CustomerTable({ entity, accountFilter = [] }: CustomerTableProps) {
  const customers = useCustomers(entity);
  const deactivate = useDeactivateCustomer();
  const deleteCustomer = useDeleteCustomer();
  const entities = useEntities() ?? [];
  const accountBalances = useAccountBalances() ?? [];
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<CustomerContract | null>(null);

  const filtered = useMemo(() => {
    if (!customers) return [];
    let result = customers;

    // Filter by bank account if specific accounts are selected
    if (accountFilter.length > 0) {
      result = result.filter((c: any) => {
        const account = c.bankAccount ?? 'Main Account';
        return accountFilter.includes(account);
      });
    }

    // Filter by search
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((c: CustomerContract) =>
        c.companyName.toLowerCase().includes(q)
      );
    }

    return result;
  }, [customers, search, accountFilter]);

  function handleEdit(customer: CustomerContract) {
    setEditingCustomer(customer);
    setFormOpen(true);
  }

  function handleAdd() {
    setEditingCustomer(null);
    setFormOpen(true);
  }

  function toggleSelect(id: string) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  }

  function toggleSelectAll() {
    if (selectedIds.length === filtered.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filtered.map((c: CustomerContract) => c._id));
    }
  }

  async function handleDeactivate(id: string) {
    try {
      await deactivate.mutateAsync({ id });
      toast.success('Customer contract deactivated');
      setSelectedIds((prev) => prev.filter((s) => s !== id));
    } catch {
      toast.error('Failed to deactivate customer');
    }
  }

  async function handleBulkDeactivate() {
    let success = 0;
    for (const id of selectedIds) {
      try {
        await deactivate.mutateAsync({ id });
        success++;
      } catch { /* skip */ }
    }
    toast.success(`${success} contract${success !== 1 ? 's' : ''} deactivated`);
    setSelectedIds([]);
  }

  async function handleDelete(id: string) {
    try {
      await deleteCustomer.mutateAsync({ id });
      toast.success('Customer contract deleted');
      setSelectedIds((prev) => prev.filter((s) => s !== id));
    } catch {
      toast.error('Failed to delete customer');
    }
  }

  async function handleBulkDelete() {
    if (!confirm(`Permanently delete ${selectedIds.length} contract${selectedIds.length !== 1 ? 's' : ''}? This cannot be undone.`)) return;
    let success = 0;
    for (const id of selectedIds) {
      try {
        await deleteCustomer.mutateAsync({ id });
        success++;
      } catch { /* skip */ }
    }
    toast.success(`${success} contract${success !== 1 ? 's' : ''} deleted`);
    setSelectedIds([]);
  }

  function formatPaymentAmount(monthlyFee: number, paymentPlan: string): string {
    const months = PAYMENT_PLAN_FREQUENCIES[paymentPlan] ?? 1;
    const amount = monthlyFee * months;
    return formatCurrency(amount);
  }

  function formatDate(dateStr: string | undefined): string {
    if (!dateStr) return 'Ongoing';
    return new Date(dateStr).toLocaleDateString('en-PH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  if (!customers) {
    return (
      <div className="flex items-center justify-center py-16 text-[#86868B]">
        Loading customer contracts...
      </div>
    );
  }

  const needsSetup = entities.length === 0 || accountBalances.length === 0;

  return (
    <div className="space-y-4">
      {needsSetup && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-amber-800">Setup required before adding contracts</p>
            <ul className="text-xs text-amber-700 mt-1 space-y-0.5">
              {entities.length === 0 && (
                <li>
                  <Link href="/dashboard/settings" className="underline hover:text-amber-900">
                    Create entities
                  </Link>{' '}
                  in Settings &gt; Entities (e.g. YAHSHUA, ABBA)
                </li>
              )}
              {accountBalances.length === 0 && (
                <li>
                  Add at least one{' '}
                  <span className="font-medium">bank balance</span>{' '}
                  in the Bank Balances tab to set your starting cash position
                </li>
              )}
            </ul>
          </div>
        </div>
      )}

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by company name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          {selectedIds.length > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">{selectedIds.length} selected</span>
              <Button
                size="sm"
                variant="outline"
                className="text-amber-600 border-amber-200 hover:bg-amber-50 text-xs"
                onClick={handleBulkDeactivate}
              >
                <XCircle className="h-3.5 w-3.5 mr-1" />
                Deactivate
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="text-red-500 border-red-200 hover:bg-red-50 text-xs"
                onClick={handleBulkDelete}
              >
                <Trash2 className="h-3.5 w-3.5 mr-1" />
                Delete
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-slate-400"
                onClick={() => setSelectedIds([])}
              >
                Clear
              </Button>
            </div>
          )}
        </div>
        <Button onClick={handleAdd} className="bg-blue-600 text-white hover:bg-blue-700" disabled={needsSetup}>
          <Plus className="h-4 w-4 mr-1" />
          Add Customer
        </Button>
      </div>

      {/* Table */}
      <div className="rounded-xl border border-[#E5E5E7] bg-white overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-200 bg-slate-50/60">
              <TableHead className="w-10">
                <Checkbox
                  checked={filtered.length > 0 && selectedIds.length === filtered.length}
                  onCheckedChange={toggleSelectAll}
                />
              </TableHead>
              <TableHead className="text-slate-500 text-xs uppercase tracking-wider font-semibold">Company Name</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold text-right">Monthly Fee</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Plan</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold text-right">Payment Amt</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Entity</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Account</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Start Date</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">End Date</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Status</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="text-center py-12 text-slate-400">
                  {search ? 'No customers match your search.' : 'No customer contracts yet.'}
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((customer: CustomerContract) => {
                const isSelected = selectedIds.includes(customer._id);
                return (
                  <TableRow
                    key={customer._id}
                    className={`cursor-pointer border-slate-100 transition-colors ${
                      isSelected
                        ? 'bg-blue-50/50'
                        : 'hover:bg-slate-50/80'
                    }`}
                    onClick={() => toggleSelect(customer._id)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSelect(customer._id)}
                      />
                    </TableCell>
                    <TableCell className="font-medium text-slate-900">
                      {customer.companyName}
                    </TableCell>
                    <TableCell className="text-right text-[#1D1D1F] tabular-nums">
                      {formatCurrency(customer.monthlyFee)}
                    </TableCell>
                    <TableCell className="text-[#1D1D1F]">{customer.paymentPlan}</TableCell>
                    <TableCell className="text-right text-[#1D1D1F] tabular-nums">
                      {formatPaymentAmount(customer.monthlyFee, customer.paymentPlan)}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={`text-[11px] font-medium px-2 py-0.5 ${
                          customer.entity === 'YAHSHUA'
                            ? 'bg-[#007AFF]/10 text-[#007AFF]'
                            : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                        }`}
                      >
                        {customer.entity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-slate-500">
                      {(customer as any).bankAccount ?? 'Main Account'}
                    </TableCell>
                    <TableCell className="text-[#86868B]">{formatDate(customer.contractStart)}</TableCell>
                    <TableCell className="text-[#86868B]">{formatDate(customer.contractEnd)}</TableCell>
                    <TableCell>
                      <StatusBadge status={customer.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(customer);
                          }}
                          title="Edit"
                        >
                          <Pencil className="h-3.5 w-3.5 text-[#007AFF]" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeactivate(customer._id);
                          }}
                          title="Deactivate"
                          disabled={customer.status === 'Inactive'}
                        >
                          <XCircle className="h-3.5 w-3.5 text-amber-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm(`Delete "${customer.companyName}" permanently?`)) {
                              handleDelete(customer._id);
                            }
                          }}
                          title="Delete permanently"
                        >
                          <Trash2 className="h-3.5 w-3.5 text-red-500" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      {/* Summary */}
      {filtered.length > 0 && (
        <div className="flex items-center justify-between text-xs text-[#86868B] px-1">
          <span>{filtered.length} contract{filtered.length !== 1 ? 's' : ''}</span>
          <span>
            Total Monthly Revenue: {formatCurrency(
              filtered
                .filter((c: CustomerContract) => c.status === 'Active')
                .reduce((sum: number, c: CustomerContract) => sum + c.monthlyFee, 0)
            )}
          </span>
        </div>
      )}

      {/* Form Dialog */}
      <CustomerForm
        open={formOpen}
        onOpenChange={setFormOpen}
        customer={editingCustomer}
      />
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    Active: 'bg-[#34C759]/10 text-[#34C759]',
    Inactive: 'bg-[#86868B]/10 text-[#86868B]',
    Pending: 'bg-[#FF9500]/10 text-[#FF9500]',
    Cancelled: 'bg-[#FF3B30]/10 text-[#FF3B30]',
  };

  return (
    <Badge className={`text-[11px] font-medium px-2 py-0.5 ${styles[status] ?? styles.Inactive}`}>
      {status}
    </Badge>
  );
}
