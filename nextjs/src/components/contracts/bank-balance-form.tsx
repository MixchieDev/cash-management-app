'use client';

import { useState } from 'react';
import { z } from 'zod';
import { useCreateBankBalance } from '@/hooks/use-contracts';
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

const balanceSchema = z.object({
  balanceDate: z.string().min(1, 'Date is required'),
  entity: z.enum(['YAHSHUA', 'ABBA']),
  balance: z.string().refine((v) => {
    const n = parseFloat(v);
    return !isNaN(n) && n >= 0;
  }, 'Balance must be a non-negative number'),
  source: z.string().min(1, 'Source is required'),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof balanceSchema>;

interface BankBalanceFormProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const emptyForm: FormData = {
  balanceDate: new Date().toISOString().split('T')[0],
  entity: 'YAHSHUA',
  balance: '',
  source: '',
  notes: '',
};

export function BankBalanceForm({ open, onOpenChange }: BankBalanceFormProps) {
  const createMutation = useCreateBankBalance();
  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});

  function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const result = balanceSchema.safeParse(form);
    if (!result.success) {
      const fieldErrors: Partial<Record<keyof FormData, string>> = {};
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof FormData;
        if (!fieldErrors[key]) fieldErrors[key] = issue.message;
      }
      setErrors(fieldErrors);
      return;
    }

    try {
      await createMutation.mutateAsync({
        balanceDate: result.data.balanceDate,
        entity: result.data.entity,
        balance: parseFloat(result.data.balance),
        source: result.data.source,
        notes: result.data.notes || undefined,
      });
      toast.success('Bank balance snapshot added');
      setForm(emptyForm);
      setErrors({});
      onOpenChange(false);
    } catch {
      toast.error('Failed to add bank balance');
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add Bank Balance Snapshot</DialogTitle>
          <DialogDescription>
            Record a bank balance snapshot to set starting cash for projections.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Date + Entity */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="balanceDate">Date</Label>
              <Input
                id="balanceDate"
                type="date"
                value={form.balanceDate}
                onChange={(e) => updateField('balanceDate', e.target.value)}
                aria-invalid={!!errors.balanceDate}
              />
              {errors.balanceDate && <p className="text-xs text-[#FF3B30]">{errors.balanceDate}</p>}
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

          {/* Balance */}
          <div className="space-y-1.5">
            <Label htmlFor="balance">Balance</Label>
            <div className="relative">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#86868B] text-sm">₱</span>
              <Input
                id="balance"
                type="number"
                step="0.01"
                min="0"
                value={form.balance}
                onChange={(e) => updateField('balance', e.target.value)}
                className="pl-7"
                placeholder="5,000,000.00"
                aria-invalid={!!errors.balance}
              />
            </div>
            {errors.balance && <p className="text-xs text-[#FF3B30]">{errors.balance}</p>}
          </div>

          {/* Source */}
          <div className="space-y-1.5">
            <Label htmlFor="source">Source</Label>
            <Input
              id="source"
              value={form.source}
              onChange={(e) => updateField('source', e.target.value)}
              placeholder="e.g. BPI Checking, BDO Savings"
              aria-invalid={!!errors.source}
            />
            {errors.source && <p className="text-xs text-[#FF3B30]">{errors.source}</p>}
          </div>

          {/* Notes */}
          <div className="space-y-1.5">
            <Label htmlFor="balanceNotes">Notes</Label>
            <Textarea
              id="balanceNotes"
              value={form.notes}
              onChange={(e) => updateField('notes', e.target.value)}
              placeholder="Optional notes..."
              className="min-h-[60px]"
            />
          </div>
        </form>

        <DialogFooter>
          <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
          <Button
            onClick={handleSubmit}
            disabled={createMutation.isPending}
            className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
          >
            {createMutation.isPending ? 'Saving...' : 'Add Balance'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
