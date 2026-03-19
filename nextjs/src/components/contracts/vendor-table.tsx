'use client';

import { useState, useMemo } from 'react';
import { formatCurrency } from '@/lib/currency';
import { useVendors, useDeactivateVendor, useDeleteVendor } from '@/hooks/use-contracts';
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
import { VendorForm } from './vendor-form';
import { toast } from 'sonner';
import { Checkbox } from '@/components/ui/checkbox';
import { Search, Plus, Pencil, XCircle, Trash2 } from 'lucide-react';
import type { VendorContract, EntityOrConsolidated } from '@/lib/types';

interface VendorTableProps {
  entity: EntityOrConsolidated;
}

function calculateMonthlyEquivalent(amount: number, frequency: string): string | null {
  if (isNaN(amount)) return null;
  switch (frequency) {
    case 'Monthly':
      return formatCurrency(amount);
    case 'Quarterly':
      return formatCurrency(amount / 3);
    case 'Annual':
      return formatCurrency(amount / 12);
    case 'Bi-annually':
      return formatCurrency(amount / 6);
    case 'One-time':
      return null;
    case 'Daily':
      return formatCurrency(amount * 30);
    case 'Weekly':
      return formatCurrency(amount * 4.33);
    case 'Bi-weekly':
      return formatCurrency(amount * 2.17);
    default:
      return formatCurrency(amount);
  }
}

function calculateMonthlyEquivalentNum(amount: number, frequency: string): number | null {
  if (isNaN(amount)) return null;
  switch (frequency) {
    case 'Monthly':
      return amount;
    case 'Quarterly':
      return amount / 3;
    case 'Annual':
      return amount / 12;
    case 'Bi-annually':
      return amount / 6;
    case 'One-time':
      return null;
    case 'Daily':
      return amount * 30;
    case 'Weekly':
      return amount * 4.33;
    case 'Bi-weekly':
      return amount * 2.17;
    default:
      return amount;
  }
}

function formatDueDay(dueDate: string): string {
  const day = parseInt(dueDate);
  if (!isNaN(day)) {
    const suffix =
      day === 1 || day === 21 || day === 31
        ? 'st'
        : day === 2 || day === 22
          ? 'nd'
          : day === 3 || day === 23
            ? 'rd'
            : 'th';
    return `${day}${suffix}`;
  }
  return dueDate;
}

const PRIORITY_LABELS: Record<number, { label: string; color: string }> = {
  1: { label: 'P1', color: 'bg-[#FF3B30]/10 text-[#FF3B30]' },
  2: { label: 'P2', color: 'bg-[#FF9500]/10 text-[#FF9500]' },
  3: { label: 'P3', color: 'bg-[#007AFF]/10 text-[#007AFF]' },
  4: { label: 'P4', color: 'bg-[#86868B]/10 text-[#86868B]' },
};

export function VendorTable({ entity }: VendorTableProps) {
  const vendors = useVendors(entity);
  const deactivate = useDeactivateVendor();
  const deleteVendor = useDeleteVendor();
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [formOpen, setFormOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState<VendorContract | null>(null);

  const filtered = useMemo(() => {
    if (!vendors) return [];
    if (!search) return vendors;
    const q = search.toLowerCase();
    return vendors.filter((v: VendorContract) =>
      v.vendorName.toLowerCase().includes(q) ||
      v.category.toLowerCase().includes(q)
    );
  }, [vendors, search]);

  function handleEdit(vendor: VendorContract) {
    setEditingVendor(vendor);
    setFormOpen(true);
  }

  function handleAdd() {
    setEditingVendor(null);
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
      setSelectedIds(filtered.map((v: VendorContract) => v._id));
    }
  }

  async function handleDeactivate(id: string) {
    try {
      await deactivate.mutateAsync({ id });
      toast.success('Vendor contract deactivated');
      setSelectedIds((prev) => prev.filter((s) => s !== id));
    } catch {
      toast.error('Failed to deactivate vendor');
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
    toast.success(`${success} vendor${success !== 1 ? 's' : ''} deactivated`);
    setSelectedIds([]);
  }

  async function handleDelete(id: string) {
    try {
      await deleteVendor.mutateAsync({ id });
      toast.success('Vendor contract deleted');
      setSelectedIds((prev) => prev.filter((s) => s !== id));
    } catch {
      toast.error('Failed to delete vendor');
    }
  }

  async function handleBulkDelete() {
    if (!confirm(`Permanently delete ${selectedIds.length} vendor${selectedIds.length !== 1 ? 's' : ''}? This cannot be undone.`)) return;
    let success = 0;
    for (const id of selectedIds) {
      try {
        await deleteVendor.mutateAsync({ id });
        success++;
      } catch { /* skip */ }
    }
    toast.success(`${success} vendor${success !== 1 ? 's' : ''} deleted`);
    setSelectedIds([]);
  }

  if (!vendors) {
    return (
      <div className="flex items-center justify-center py-16 text-[#86868B]">
        Loading vendor contracts...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search vendors or categories..."
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
        <Button onClick={handleAdd} className="bg-blue-600 text-white hover:bg-blue-700">
          <Plus className="h-4 w-4 mr-1" />
          Add Vendor
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
              <TableHead className="text-slate-500 text-xs uppercase tracking-wider font-semibold">Vendor Name</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Category</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold text-right">Amount</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Frequency</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Due Day</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold text-right">Monthly Equiv.</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Entity</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Priority</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold">Status</TableHead>
              <TableHead className="text-[#86868B] text-xs uppercase tracking-wider font-semibold w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11} className="text-center py-12 text-slate-400">
                  {search ? 'No vendors match your search.' : 'No vendor contracts yet.'}
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((vendor: VendorContract) => {
                const isSelected = selectedIds.includes(vendor._id);
                const monthlyEquiv = calculateMonthlyEquivalent(vendor.amount, vendor.frequency);
                const priority = PRIORITY_LABELS[vendor.priority] ?? PRIORITY_LABELS[4];
                return (
                  <TableRow
                    key={vendor._id}
                    className={`cursor-pointer border-slate-100 transition-colors ${
                      isSelected ? 'bg-blue-50/50' : 'hover:bg-slate-50/80'
                    }`}
                    onClick={() => toggleSelect(vendor._id)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => toggleSelect(vendor._id)}
                      />
                    </TableCell>
                    <TableCell className="font-medium text-slate-900">{vendor.vendorName}</TableCell>
                    <TableCell className="text-[#1D1D1F]">{vendor.category}</TableCell>
                    <TableCell className="text-right text-[#1D1D1F] tabular-nums">
                      {formatCurrency(vendor.amount)}
                    </TableCell>
                    <TableCell className="text-[#1D1D1F]">{vendor.frequency}</TableCell>
                    <TableCell className="text-[#1D1D1F]">{formatDueDay(vendor.dueDate)}</TableCell>
                    <TableCell className="text-right text-[#86868B] tabular-nums">
                      {monthlyEquiv ?? <span className="text-[#86868B]/60">&mdash;</span>}
                    </TableCell>
                    <TableCell>
                      <Badge
                        className={`text-[11px] font-medium px-2 py-0.5 ${
                          vendor.entity === 'YAHSHUA'
                            ? 'bg-[#007AFF]/10 text-[#007AFF]'
                            : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                        }`}
                      >
                        {vendor.entity}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={`text-[11px] font-semibold px-2 py-0.5 ${priority.color}`}>
                        {priority.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <VendorStatusBadge status={vendor.status} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleEdit(vendor);
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
                            handleDeactivate(vendor._id);
                          }}
                          title="Deactivate"
                          disabled={vendor.status === 'Inactive'}
                        >
                          <XCircle className="h-3.5 w-3.5 text-amber-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm(`Delete "${vendor.vendorName}" permanently?`)) {
                              handleDelete(vendor._id);
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
            Total Monthly Cost: {formatCurrency(
              filtered
                .filter((v: VendorContract) => v.status === 'Active')
                .reduce((sum: number, v: VendorContract) => {
                  const equiv = calculateMonthlyEquivalentNum(v.amount, v.frequency);
                  return equiv != null ? sum + equiv : sum;
                }, 0)
            )}
          </span>
        </div>
      )}

      {/* Form Dialog */}
      <VendorForm
        open={formOpen}
        onOpenChange={setFormOpen}
        vendor={editingVendor}
      />
    </div>
  );
}

function VendorStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    Active: 'bg-[#34C759]/10 text-[#34C759]',
    Inactive: 'bg-[#86868B]/10 text-[#86868B]',
    Paid: 'bg-[#007AFF]/10 text-[#007AFF]',
    Pending: 'bg-[#FF9500]/10 text-[#FF9500]',
  };

  return (
    <Badge className={`text-[11px] font-medium px-2 py-0.5 ${styles[status] ?? styles.Inactive}`}>
      {status}
    </Badge>
  );
}
