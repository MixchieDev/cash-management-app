'use client';

import { useEffect, useState } from 'react';
import { z } from 'zod';
import { useCreateVendor, useUpdateVendor } from '@/hooks/use-contracts';
import { VALID_EXPENSE_CATEGORIES, VALID_EXPENSE_FREQUENCIES, EXPENSE_CATEGORIES } from '@/lib/constants';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { VendorContract } from '@/lib/types';
import { BankAccountSelect } from './bank-account-select';
import { useEntities } from '@/hooks/use-entities';

const vendorSchema = z.object({
  vendorName: z.string().min(1, 'Vendor name is required'),
  category: z.string().min(1, 'Category is required'),
  amount: z.string().refine((v) => {
    const n = parseFloat(v);
    return !isNaN(n) && n > 0;
  }, 'Amount must be a positive number'),
  frequency: z.string().min(1, 'Frequency is required'),
  dueDate: z.string().min(1, 'Due date/day is required'),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  entity: z.string().min(1, 'Entity is required'),
  priority: z.string().refine((v) => {
    const n = parseInt(v);
    return n >= 1 && n <= 4;
  }, 'Priority must be 1-4'),
  flexibilityDays: z.string().optional(),
  status: z.string().min(1, 'Status is required'),
  notes: z.string().optional(),
  bankAccount: z.string().optional(),
});

type FormData = z.infer<typeof vendorSchema>;

interface VendorFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  vendor: VendorContract | null;
}

const PRIORITY_OPTIONS = [
  { value: '1', label: 'P1 - Non-negotiable (Payroll)' },
  { value: '2', label: 'P2 - Contractual (Loans)' },
  { value: '3', label: 'P3 - Medium flexibility (Software/Tech)' },
  { value: '4', label: 'P4 - High flexibility (Operations)' },
];

const VENDOR_STATUSES = ['Active', 'Inactive', 'Paid', 'Pending'];

const emptyForm: FormData = {
  vendorName: '',
  category: 'Operations',
  amount: '',
  frequency: 'Monthly',
  dueDate: '',
  startDate: '',
  endDate: '',
  entity: 'YAHSHUA',
  priority: '4',
  flexibilityDays: '',
  status: 'Active',
  notes: '',
  bankAccount: 'Main Account',
};

export function VendorForm({ open, onOpenChange, vendor }: VendorFormProps) {
  const createMutation = useCreateVendor();
  const updateMutation = useUpdateVendor();
  const entities = useEntities() ?? [];
  const isEditing = !!vendor;

  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  useEffect(() => {
    if (vendor) {
      setForm({
        vendorName: vendor.vendorName,
        category: vendor.category,
        amount: vendor.amount.toString(),
        frequency: vendor.frequency,
        dueDate: vendor.dueDate,
        startDate: vendor.startDate ?? '',
        endDate: vendor.endDate ?? '',
        entity: vendor.entity,
        priority: vendor.priority.toString(),
        flexibilityDays: vendor.flexibilityDays.toString(),
        status: vendor.status,
        notes: vendor.notes ?? '',
        bankAccount: (vendor as any).bankAccount ?? 'Main Account',
      });
    } else {
      setForm({
        ...emptyForm,
        entity: entities.length > 0 ? entities[0].shortCode : '',
      });
    }
    setErrors({});
  }, [vendor, open, entities]);

  function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    }

    // Auto-fill priority and flexibility when category changes
    if (key === 'category' && typeof value === 'string') {
      const catInfo = EXPENSE_CATEGORIES[value];
      if (catInfo) {
        setForm((prev) => ({
          ...prev,
          [key]: value,
          priority: catInfo.priority.toString(),
          flexibilityDays: catInfo.flexibilityDays.toString(),
        }));
      }
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const result = vendorSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof FormData, string>> = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof FormData;
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    // Convert due day (e.g. "15") to ISO date anchored to current month
    let dueDate = result.data.dueDate;
    if (/^\d{1,2}$/.test(dueDate.trim())) {
      const day = parseInt(dueDate.trim(), 10);
      const now = new Date();
      const y = now.getFullYear();
      const m = String(now.getMonth() + 1).padStart(2, '0');
      const d = String(Math.min(day, 28)).padStart(2, '0');
      dueDate = `${y}-${m}-${d}`;
    }

    const payload = {
      vendorName: result.data.vendorName,
      category: result.data.category,
      amount: parseFloat(result.data.amount),
      frequency: result.data.frequency,
      dueDate,
      startDate: result.data.startDate || undefined,
      endDate: result.data.endDate || undefined,
      entity: result.data.entity,
      priority: parseInt(result.data.priority),
      flexibilityDays: result.data.flexibilityDays ? parseInt(result.data.flexibilityDays) : 0,
      status: result.data.status,
      notes: result.data.notes || undefined,
      bankAccount: result.data.bankAccount || 'Main Account',
    };

    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: vendor._id, ...payload });
        toast.success('Vendor contract updated');
      } else {
        await createMutation.mutateAsync({ ...payload, source: 'manual' });
        toast.success('Vendor contract created');
      }
      onOpenChange(false);
    } catch {
      toast.error(isEditing ? 'Failed to update vendor' : 'Failed to create vendor');
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Vendor Contract' : 'Add Vendor Contract'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the vendor contract details below.'
              : 'Enter the details for the new vendor contract.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto px-0.5">
          {/* Vendor Name */}
          <div className="space-y-1.5">
            <Label htmlFor="vendorName">Vendor Name</Label>
            <Input
              id="vendorName"
              value={form.vendorName}
              onChange={(e) => updateField('vendorName', e.target.value)}
              placeholder="e.g. AWS, Google Workspace"
              aria-invalid={!!errors.vendorName}
            />
            {errors.vendorName && <p className="text-xs text-[#FF3B30]">{errors.vendorName}</p>}
          </div>

          {/* Category + Frequency */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Category</Label>
              <Select
                value={form.category}
                onValueChange={(v: string | null) => v && updateField('category', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VALID_EXPENSE_CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Frequency</Label>
              <Select
                value={form.frequency}
                onValueChange={(v: string | null) => v && updateField('frequency', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VALID_EXPENSE_FREQUENCIES.map((freq) => (
                    <SelectItem key={freq} value={freq}>
                      {freq}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Amount + Due Day */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="amount">Amount</Label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#86868B] text-sm">₱</span>
                <Input
                  id="amount"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.amount}
                  onChange={(e) => updateField('amount', e.target.value)}
                  className="pl-7"
                  placeholder="10,000.00"
                  aria-invalid={!!errors.amount}
                />
              </div>
              {errors.amount && <p className="text-xs text-[#FF3B30]">{errors.amount}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="dueDate">Due Date</Label>
              <Input
                id="dueDate"
                type="date"
                value={form.dueDate}
                onChange={(e) => updateField('dueDate', e.target.value)}
                aria-invalid={!!errors.dueDate}
              />
              {errors.dueDate && <p className="text-xs text-[#FF3B30]">{errors.dueDate}</p>}
            </div>
          </div>

          {/* Entity + Priority */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Entity</Label>
              <Select
                value={form.entity}
                onValueChange={(v: string | null) => v && updateField('entity', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select entity" />
                </SelectTrigger>
                <SelectContent>
                  {entities.map((ent: any) => (
                    <SelectItem key={ent.shortCode} value={ent.shortCode}>
                      <span className="flex items-center gap-2">
                        <span className="h-2 w-2 rounded-full" style={{ backgroundColor: ent.color ?? '#64748b' }} />
                        {ent.shortCode}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Bank Account */}
          <BankAccountSelect
            entity={form.entity}
            value={form.bankAccount ?? 'Main Account'}
            onChange={(v) => updateField('bankAccount', v)}
          />

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Priority</Label>
              <Select
                value={form.priority}
                onValueChange={(v: string | null) => v && updateField('priority', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Start Date + End Date */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="startDate">Start Date (Optional)</Label>
              <Input
                id="startDate"
                type="date"
                value={form.startDate}
                onChange={(e) => updateField('startDate', e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="endDate">End Date (Optional)</Label>
              <Input
                id="endDate"
                type="date"
                value={form.endDate}
                onChange={(e) => updateField('endDate', e.target.value)}
              />
            </div>
          </div>

          {/* Status + Flexibility Days */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Status</Label>
              <Select
                value={form.status}
                onValueChange={(v: string | null) => v && updateField('status', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VENDOR_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="flexibilityDays">Flexibility Days</Label>
              <Input
                id="flexibilityDays"
                type="number"
                min="0"
                value={form.flexibilityDays}
                onChange={(e) => updateField('flexibilityDays', e.target.value)}
                placeholder="0"
              />
            </div>
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label htmlFor="vendorNotes">Notes</Label>
            <Textarea
              id="vendorNotes"
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              placeholder="Optional notes about this vendor contract..."
              className="min-h-[60px]"
            />
          </div>
        </form>

        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
          <Button
            onClick={handleSubmit}
            disabled={isPending}
            className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
          >
            {isPending ? 'Saving...' : isEditing ? 'Update Contract' : 'Create Contract'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
