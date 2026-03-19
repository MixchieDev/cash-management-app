'use client';

import { useEffect, useState } from 'react';
import { z } from 'zod';
import { useCreateCustomer, useUpdateCustomer } from '@/hooks/use-contracts';
import { VALID_PAYMENT_PLANS, VALID_CONTRACT_STATUSES } from '@/lib/constants';
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
import type { CustomerContract } from '@/lib/types';

const customerSchema = z.object({
  companyName: z.string().min(1, 'Company name is required'),
  monthlyFee: z.string().refine((v) => {
    const n = parseFloat(v);
    return !isNaN(n) && n > 0;
  }, 'Monthly fee must be a positive number'),
  paymentPlan: z.string().min(1, 'Payment plan is required'),
  whoAcquired: z.string().min(1, 'Acquisition source is required'),
  entity: z.string().min(1, 'Entity is required'),
  contractStart: z.string().min(1, 'Start date is required'),
  contractEnd: z.string().optional(),
  status: z.string().min(1, 'Status is required'),
  invoiceDay: z.string().optional(),
  reliabilityScore: z.string().optional(),
  notes: z.string().optional(),
  bankAccount: z.string().optional(),
});

type FormData = z.infer<typeof customerSchema>;

interface CustomerFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  customer: CustomerContract | null;
}

const ACQUISITION_SOURCES = ['RCBC Partner', 'Globe Partner', 'YOWI', 'TAI', 'PEI'];

const emptyForm: FormData = {
  companyName: '',
  monthlyFee: '',
  paymentPlan: 'Monthly',
  whoAcquired: '',
  entity: 'YAHSHUA',
  contractStart: '',
  contractEnd: '',
  status: 'Active',
  invoiceDay: '',
  reliabilityScore: '0.80',
  notes: '',
  bankAccount: 'RCBC Current',
};

export function CustomerForm({ open, onOpenChange, customer }: CustomerFormProps) {
  const createMutation = useCreateCustomer();
  const updateMutation = useUpdateCustomer();
  const isEditing = !!customer;

  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  useEffect(() => {
    if (customer) {
      setForm({
        companyName: customer.companyName,
        monthlyFee: customer.monthlyFee.toString(),
        paymentPlan: customer.paymentPlan,
        whoAcquired: customer.whoAcquired,
        entity: customer.entity,
        contractStart: customer.contractStart,
        contractEnd: customer.contractEnd ?? '',
        status: customer.status,
        invoiceDay: customer.invoiceDay?.toString() ?? '',
        reliabilityScore: customer.reliabilityScore?.toString() ?? '0.80',
        notes: customer.notes ?? '',
        bankAccount: (customer as any).bankAccount ?? 'RCBC Current',
      });
    } else {
      setForm(emptyForm);
    }
    setErrors({});
  }, [customer, open]);

  function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const result = customerSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof FormData, string>> = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof FormData;
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    const payload = {
      companyName: result.data.companyName,
      monthlyFee: parseFloat(result.data.monthlyFee),
      paymentPlan: result.data.paymentPlan,
      whoAcquired: result.data.whoAcquired,
      entity: result.data.entity,
      contractStart: result.data.contractStart,
      contractEnd: result.data.contractEnd || undefined,
      status: result.data.status,
      invoiceDay: result.data.invoiceDay ? parseInt(result.data.invoiceDay) : undefined,
      reliabilityScore: parseFloat(result.data.reliabilityScore || '0.80'),
      notes: result.data.notes || undefined,
      bankAccount: result.data.bankAccount || 'RCBC Current',
    };

    try {
      if (isEditing) {
        await updateMutation.mutateAsync({ id: customer._id, ...payload });
        toast.success('Customer contract updated');
      } else {
        await createMutation.mutateAsync({ ...payload, source: 'manual' });
        toast.success('Customer contract created');
      }
      onOpenChange(false);
    } catch {
      toast.error(isEditing ? 'Failed to update customer' : 'Failed to create customer');
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Customer Contract' : 'Add Customer Contract'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the customer contract details below.'
              : 'Enter the details for the new customer contract.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 max-h-[60vh] overflow-y-auto px-0.5">
          {/* Company Name */}
          <div className="space-y-1.5">
            <Label htmlFor="companyName">Company Name</Label>
            <Input
              id="companyName"
              value={form.companyName}
              onChange={(e) => updateField('companyName', e.target.value)}
              placeholder="e.g. Acme Corp"
              aria-invalid={!!errors.companyName}
            />
            {errors.companyName && <p className="text-xs text-[#FF3B30]">{errors.companyName}</p>}
          </div>

          {/* Monthly Fee + Payment Plan */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="monthlyFee">Monthly Fee</Label>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#86868B] text-sm">₱</span>
                <Input
                  id="monthlyFee"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.monthlyFee}
                  onChange={(e) => updateField('monthlyFee', e.target.value)}
                  className="pl-7"
                  placeholder="50,000.00"
                  aria-invalid={!!errors.monthlyFee}
                />
              </div>
              {errors.monthlyFee && <p className="text-xs text-[#FF3B30]">{errors.monthlyFee}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Payment Plan</Label>
              <Select
                value={form.paymentPlan}
                onValueChange={(v: string | null) => v && updateField('paymentPlan', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {VALID_PAYMENT_PLANS.map((plan) => (
                    <SelectItem key={plan} value={plan}>
                      {plan}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Who Acquired + Entity */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>Acquired By</Label>
              <Select
                value={form.whoAcquired}
                onValueChange={(v: string | null) => v && updateField('whoAcquired', v)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select source" />
                </SelectTrigger>
                <SelectContent>
                  {ACQUISITION_SOURCES.map((src) => (
                    <SelectItem key={src} value={src}>
                      {src}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.whoAcquired && <p className="text-xs text-[#FF3B30]">{errors.whoAcquired}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Entity</Label>
              <Select
                value={form.entity}
                onValueChange={(v: string | null) => v && updateField('entity', v as 'YAHSHUA' | 'ABBA')}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="YAHSHUA">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-[#007AFF]" />
                      YAHSHUA
                    </span>
                  </SelectItem>
                  <SelectItem value="ABBA">
                    <span className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-[#AF52DE]" />
                      ABBA
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Bank Account */}
          <div className="space-y-1.5">
            <Label htmlFor="bankAccount">Bank Account</Label>
            <Input
              id="bankAccount"
              value={form.bankAccount ?? 'RCBC Current'}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateField('bankAccount', e.target.value)}
              placeholder="e.g. RCBC Current, BDO Savings"
            />
          </div>

          {/* Contract Start + End */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="contractStart">Start Date</Label>
              <Input
                id="contractStart"
                type="date"
                value={form.contractStart}
                onChange={(e) => updateField('contractStart', e.target.value)}
                aria-invalid={!!errors.contractStart}
              />
              {errors.contractStart && <p className="text-xs text-[#FF3B30]">{errors.contractStart}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="contractEnd">End Date (Optional)</Label>
              <Input
                id="contractEnd"
                type="date"
                value={form.contractEnd}
                onChange={(e) => updateField('contractEnd', e.target.value)}
              />
            </div>
          </div>

          {/* Status + Invoice Day */}
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
                  {VALID_CONTRACT_STATUSES.map((status) => (
                    <SelectItem key={status} value={status}>
                      {status}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="invoiceDay">Invoice Day (1-28)</Label>
              <Input
                id="invoiceDay"
                type="number"
                min={1}
                max={28}
                value={form.invoiceDay}
                onChange={(e) => updateField('invoiceDay', e.target.value)}
                placeholder="15"
              />
            </div>
          </div>

          {/* Reliability Score */}
          <div className="space-y-1.5">
            <Label htmlFor="reliabilityScore">Reliability Score (0.00 - 1.00)</Label>
            <Input
              id="reliabilityScore"
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={form.reliabilityScore}
              onChange={(e) => updateField('reliabilityScore', e.target.value)}
              placeholder="0.80"
            />
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              placeholder="Optional notes about this contract..."
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
