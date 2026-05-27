'use client';

import { useState } from 'react';
import { z } from 'zod';
import {
  useAdhocEvents,
  useCreateAdhocEvent,
  useDeleteAdhocEvent,
} from '@/hooks/use-contracts';
import { toast } from 'sonner';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowDownToLine,
  ArrowUpFromLine,
  Plus,
  Trash2,
} from 'lucide-react';
import { formatCurrency } from '@/lib/currency';

interface AdjustmentManagerProps {
  entity: string;
}

const schema = z.object({
  eventType: z.enum(['inflow', 'outflow']),
  date: z.string().min(1, 'Date is required'),
  amount: z.string().refine((v) => {
    const n = parseFloat(v);
    return !isNaN(n) && n > 0;
  }, 'Amount must be a positive number'),
  description: z.string().min(1, 'Description is required'),
  category: z.string().optional(),
  entity: z.enum(['YAHSHUA', 'ABBA']),
  bankAccount: z.string().optional(),
  confidence: z.enum(['committed', 'likely', 'possible']),
  notes: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const emptyForm: FormData = {
  eventType: 'inflow',
  date: '',
  amount: '',
  description: '',
  category: '',
  entity: 'YAHSHUA',
  bankAccount: 'Main Account',
  confidence: 'committed',
  notes: '',
};

const OUTFLOW_CATEGORIES = [
  'Payroll',
  'Loans',
  'Software/Tech',
  'Operations',
  'Rent',
  'Utilities',
  'Tax',
  'Other',
];

export function AdjustmentManager({ entity }: AdjustmentManagerProps) {
  const events = useAdhocEvents(entity);
  const createMutation = useCreateAdhocEvent();
  const deleteMutation = useDeleteAdhocEvent();

  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [showForm, setShowForm] = useState(false);

  function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    const result = schema.safeParse(form);
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
        eventType: result.data.eventType,
        date: result.data.date,
        amount: parseFloat(result.data.amount),
        description: result.data.description,
        category: result.data.eventType === 'outflow' ? result.data.category || undefined : undefined,
        entity: result.data.entity,
        bankAccount: result.data.bankAccount || undefined,
        confidence: result.data.confidence,
        notes: result.data.notes || undefined,
      });
      toast.success('Adjustment created');
      setForm(emptyForm);
      setErrors({});
      setShowForm(false);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to create adjustment');
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync({ id });
      toast.success('Adjustment removed');
    } catch {
      toast.error('Failed to remove adjustment');
    }
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr + 'T00:00:00Z').toLocaleDateString('en-PH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  const isLoading = !events;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#86868B]">
            One-off inflows or outflows that aren&apos;t tied to a recurring contract —
            tax refunds, owner injections, settlements, equipment purchases, etc.
          </p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
        >
          <Plus className="h-4 w-4" data-icon="inline-start" />
          {showForm ? 'Hide Form' : 'New Adjustment'}
        </Button>
      </div>

      {showForm && (
        <Card className="border border-[#E5E5E7] shadow-sm">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <Select
                    value={form.eventType}
                    onValueChange={(v: string | null) =>
                      v && updateField('eventType', v as 'inflow' | 'outflow')
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="inflow">
                        <span className="flex items-center gap-2">
                          <ArrowDownToLine className="h-3.5 w-3.5 text-[#34C759]" />
                          Inflow (money in)
                        </span>
                      </SelectItem>
                      <SelectItem value="outflow">
                        <span className="flex items-center gap-2">
                          <ArrowUpFromLine className="h-3.5 w-3.5 text-[#FF3B30]" />
                          Outflow (money out)
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label>Entity</Label>
                  <Select
                    value={form.entity}
                    onValueChange={(v: string | null) =>
                      v && updateField('entity', v as 'YAHSHUA' | 'ABBA')
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="YAHSHUA">YAHSHUA</SelectItem>
                      <SelectItem value="ABBA">ABBA</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="adj-description">Description</Label>
                <Input
                  id="adj-description"
                  value={form.description}
                  onChange={(e) => updateField('description', e.target.value)}
                  placeholder="e.g. BIR tax refund, owner cash injection, equipment purchase"
                  aria-invalid={!!errors.description}
                />
                {errors.description && <p className="text-xs text-[#FF3B30]">{errors.description}</p>}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="adj-date">Date</Label>
                  <Input
                    id="adj-date"
                    type="date"
                    value={form.date}
                    onChange={(e) => updateField('date', e.target.value)}
                    aria-invalid={!!errors.date}
                  />
                  {errors.date && <p className="text-xs text-[#FF3B30]">{errors.date}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="adj-amount">Amount</Label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#86868B] text-sm">₱</span>
                    <Input
                      id="adj-amount"
                      type="number"
                      step="0.01"
                      min="0"
                      value={form.amount}
                      onChange={(e) => updateField('amount', e.target.value)}
                      className="pl-7"
                      placeholder="50,000.00"
                      aria-invalid={!!errors.amount}
                    />
                  </div>
                  {errors.amount && <p className="text-xs text-[#FF3B30]">{errors.amount}</p>}
                </div>
              </div>

              {form.eventType === 'outflow' && (
                <div className="space-y-1.5">
                  <Label>Category (Optional)</Label>
                  <Select
                    value={form.category || 'none'}
                    onValueChange={(v: string | null) =>
                      v && updateField('category', v === 'none' ? '' : v)
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">— No category —</SelectItem>
                      {OUTFLOW_CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>{c}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Bank Account (Optional)</Label>
                  <Input
                    value={form.bankAccount}
                    onChange={(e) => updateField('bankAccount', e.target.value)}
                    placeholder="Main Account"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Confidence</Label>
                  <Select
                    value={form.confidence}
                    onValueChange={(v: string | null) =>
                      v && updateField('confidence', v as 'committed' | 'likely' | 'possible')
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="committed">Committed</SelectItem>
                      <SelectItem value="likely">Likely</SelectItem>
                      <SelectItem value="possible">Possible</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="adj-notes">Notes (Optional)</Label>
                <Textarea
                  id="adj-notes"
                  value={form.notes}
                  onChange={(e) => updateField('notes', e.target.value)}
                  placeholder="Context — who, why, any caveats"
                  className="min-h-[60px]"
                />
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="outline" type="button" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Adjustment'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Separator className="bg-[#E5E5E7]" />

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#1D1D1F]">
          Active Adjustments
          {(events ?? []).length > 0 && (
            <span className="ml-2 text-xs font-normal text-[#86868B]">
              ({(events ?? []).length})
            </span>
          )}
        </h3>

        {isLoading ? (
          <div className="text-center py-8 text-[#86868B]">Loading adjustments...</div>
        ) : (events ?? []).length === 0 ? (
          <Card className="border border-[#E5E5E7]">
            <CardContent className="py-8 text-center text-[#86868B]">
              No adjustments yet. Create one for any one-off cash event not tied to a contract.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {(events ?? [])
              .slice()
              .sort((a, b) => a.date.localeCompare(b.date))
              .map((ev) => (
                <AdjustmentCard
                  key={ev._id}
                  event={ev}
                  onDelete={handleDelete}
                  formatDate={formatDate}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

function AdjustmentCard({
  event,
  onDelete,
  formatDate,
}: {
  event: {
    _id: string;
    eventType: string;
    date: string;
    amount: number;
    description: string;
    category?: string;
    entity: string;
    confidence?: string;
    notes?: string;
  };
  onDelete: (id: string) => void;
  formatDate: (d: string) => string;
}) {
  const isInflow = event.eventType === 'inflow';
  const conf = event.confidence ?? 'committed';

  return (
    <Card className="border border-[#E5E5E7] hover:border-[#007AFF]/20 transition-colors">
      <CardContent className="py-3 px-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0 flex-1">
            <div
              className={`flex-shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${
                isInflow ? 'bg-[#34C759]/10' : 'bg-[#FF3B30]/10'
              }`}
            >
              {isInflow ? (
                <ArrowDownToLine className="h-4 w-4 text-[#34C759]" />
              ) : (
                <ArrowUpFromLine className="h-4 w-4 text-[#FF3B30]" />
              )}
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-sm text-[#1D1D1F] truncate">
                  {event.description}
                </span>
                <Badge
                  className={`text-[10px] px-1.5 py-0 ${
                    event.entity === 'YAHSHUA'
                      ? 'bg-[#007AFF]/10 text-[#007AFF]'
                      : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                  }`}
                >
                  {event.entity}
                </Badge>
                {event.category && (
                  <Badge className="text-[10px] px-1.5 py-0 bg-[#86868B]/10 text-[#86868B]">
                    {event.category}
                  </Badge>
                )}
                {conf !== 'committed' && (
                  <Badge className="text-[10px] px-1.5 py-0 bg-[#FF9500]/10 text-[#FF9500]">
                    {conf}
                  </Badge>
                )}
              </div>
              <div className="flex items-center gap-3 mt-0.5 text-xs text-[#86868B]">
                <span>{formatDate(event.date)}</span>
                <span className={isInflow ? 'text-[#34C759] font-semibold' : 'text-[#FF3B30] font-semibold'}>
                  {isInflow ? '+' : '−'}{formatCurrency(event.amount).replace('-', '')}
                </span>
              </div>
              {event.notes && (
                <p className="text-xs text-[#86868B] mt-0.5 truncate max-w-md">
                  {event.notes}
                </p>
              )}
            </div>
          </div>

          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => onDelete(event._id)}
            title="Remove adjustment"
          >
            <Trash2 className="h-3.5 w-3.5 text-[#FF3B30]" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
