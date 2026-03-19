'use client';

import { useState } from 'react';
import { z } from 'zod';
import {
  useOverrides,
  useCreateOverride,
  useDeleteOverride,
  useCustomers,
  useVendors,
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
  ArrowRight,
  Ban,
  Trash2,
  Users,
  Building2,
  Plus,
} from 'lucide-react';
import type { EntityOrConsolidated, PaymentOverride, CustomerContract, VendorContract } from '@/lib/types';

interface OverrideManagerProps {
  entity: string;
}

const overrideSchema = z.object({
  overrideType: z.enum(['customer', 'vendor']),
  contractId: z.string().min(1, 'Select a contract'),
  originalDate: z.string().min(1, 'Payment date is required'),
  action: z.enum(['move', 'skip']),
  newDate: z.string().optional(),
  entity: z.enum(['YAHSHUA', 'ABBA']),
  reason: z.string().optional(),
});

type FormData = z.infer<typeof overrideSchema>;

const emptyForm: FormData = {
  overrideType: 'customer',
  contractId: '',
  originalDate: '',
  action: 'move',
  newDate: '',
  entity: 'YAHSHUA',
  reason: '',
};

export function OverrideManager({ entity }: OverrideManagerProps) {
  const overrides = useOverrides(entity);
  const customers = useCustomers(entity);
  const vendors = useVendors(entity);
  const createMutation = useCreateOverride();
  const deleteMutation = useDeleteOverride();

  const [form, setForm] = useState<FormData>(emptyForm);
  const [errors, setErrors] = useState<Partial<Record<keyof FormData, string>>>({});
  const [showForm, setShowForm] = useState(false);

  function updateField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }));
    }
    // Reset contract selection when type changes
    if (key === 'overrideType') {
      setForm((prev) => ({ ...prev, [key]: value, contractId: '' }));
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    // Validate new date required if action is 'move'
    if (form.action === 'move' && !form.newDate) {
      setErrors((prev) => ({ ...prev, newDate: 'New date is required for move action' }));
      return;
    }

    const result = overrideSchema.safeParse(form);
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
        overrideType: result.data.overrideType,
        contractId: result.data.contractId,
        originalDate: result.data.originalDate,
        action: result.data.action,
        newDate: result.data.action === 'move' ? result.data.newDate : undefined,
        entity: result.data.entity,
        reason: result.data.reason || undefined,
      });
      toast.success('Payment override created');
      setForm(emptyForm);
      setErrors({});
      setShowForm(false);
    } catch {
      toast.error('Failed to create override');
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync({ id });
      toast.success('Override removed');
    } catch {
      toast.error('Failed to remove override');
    }
  }

  const contractOptions =
    form.overrideType === 'customer'
      ? (customers ?? []).map((c: CustomerContract) => ({ id: c._id, name: c.companyName, entity: c.entity }))
      : (vendors ?? []).map((v: VendorContract) => ({ id: v._id, name: v.vendorName, entity: v.entity }));

  function getContractName(override: PaymentOverride): string {
    if (override.overrideType === 'customer') {
      const c = (customers ?? []).find((c: CustomerContract) => c._id === override.contractId);
      return c?.companyName ?? `Customer #${override.contractId}`;
    }
    const v = (vendors ?? []).find((v: VendorContract) => v._id === override.contractId);
    return v?.vendorName ?? `Vendor #${override.contractId}`;
  }

  function formatDate(dateStr: string): string {
    return new Date(dateStr).toLocaleDateString('en-PH', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  const isLoading = !overrides;

  return (
    <div className="space-y-6">
      {/* Header + Add Button */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm text-[#86868B]">
            Create one-off payment date adjustments. Move or skip individual payments without changing recurring schedules.
          </p>
        </div>
        <Button
          onClick={() => setShowForm(!showForm)}
          className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
        >
          <Plus className="h-4 w-4" data-icon="inline-start" />
          {showForm ? 'Hide Form' : 'New Override'}
        </Button>
      </div>

      {/* Create Form */}
      {showForm && (
        <Card className="border border-[#E5E5E7] shadow-sm">
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Type + Entity */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label>Type</Label>
                  <Select
                    value={form.overrideType}
                    onValueChange={(v: string | null) => v && updateField('overrideType', v as 'customer' | 'vendor')}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="customer">
                        <span className="flex items-center gap-2">
                          <Users className="h-3.5 w-3.5" />
                          Customer
                        </span>
                      </SelectItem>
                      <SelectItem value="vendor">
                        <span className="flex items-center gap-2">
                          <Building2 className="h-3.5 w-3.5" />
                          Vendor
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
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

              {/* Contract Selection */}
              <div className="space-y-1.5">
                <Label>Contract</Label>
                <Select
                  value={form.contractId}
                  onValueChange={(v: string | null) => v && updateField('contractId', v)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Select a contract..." />
                  </SelectTrigger>
                  <SelectContent>
                    {contractOptions.length === 0 ? (
                      <SelectItem value="_none" disabled>
                        No contracts available
                      </SelectItem>
                    ) : (
                      contractOptions.map((opt: { id: string; name: string; entity: string }) => (
                        <SelectItem key={opt.id} value={opt.id}>
                          <span className="flex items-center gap-2">
                            <Badge
                              className={`text-[10px] px-1.5 py-0 ${
                                opt.entity === 'YAHSHUA'
                                  ? 'bg-[#007AFF]/10 text-[#007AFF]'
                                  : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                              }`}
                            >
                              {opt.entity}
                            </Badge>
                            {opt.name}
                          </span>
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
                {errors.contractId && <p className="text-xs text-[#FF3B30]">{errors.contractId}</p>}
              </div>

              {/* Action + Dates */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <Label>Action</Label>
                  <Select
                    value={form.action}
                    onValueChange={(v: string | null) => v && updateField('action', v as 'move' | 'skip')}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="move">
                        <span className="flex items-center gap-2">
                          <ArrowRight className="h-3.5 w-3.5" />
                          Move
                        </span>
                      </SelectItem>
                      <SelectItem value="skip">
                        <span className="flex items-center gap-2">
                          <Ban className="h-3.5 w-3.5" />
                          Skip
                        </span>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="originalDate">Original Date</Label>
                  <Input
                    id="originalDate"
                    type="date"
                    value={form.originalDate}
                    onChange={(e) => updateField('originalDate', e.target.value)}
                    aria-invalid={!!errors.originalDate}
                  />
                  {errors.originalDate && <p className="text-xs text-[#FF3B30]">{errors.originalDate}</p>}
                </div>
                {form.action === 'move' && (
                  <div className="space-y-1.5">
                    <Label htmlFor="newDate">New Date</Label>
                    <Input
                      id="newDate"
                      type="date"
                      value={form.newDate}
                      onChange={(e) => updateField('newDate', e.target.value)}
                      aria-invalid={!!errors.newDate}
                    />
                    {errors.newDate && <p className="text-xs text-[#FF3B30]">{errors.newDate}</p>}
                  </div>
                )}
              </div>

              {/* Reason */}
              <div className="space-y-1.5">
                <Label htmlFor="reason">Reason (Optional)</Label>
                <Textarea
                  id="reason"
                  value={form.reason}
                  onChange={(e) => updateField('reason', e.target.value)}
                  placeholder="e.g. Client requested payment delay, billing dispute..."
                  className="min-h-[60px]"
                />
              </div>

              {/* Submit */}
              <div className="flex justify-end gap-2">
                <Button variant="outline" type="button" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Override'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <Separator className="bg-[#E5E5E7]" />

      {/* Active Overrides List */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-[#1D1D1F]">
          Active Overrides
          {(overrides ?? []).length > 0 && (
            <span className="ml-2 text-xs font-normal text-[#86868B]">
              ({(overrides ?? []).length})
            </span>
          )}
        </h3>

        {isLoading ? (
          <div className="text-center py-8 text-[#86868B]">Loading overrides...</div>
        ) : (overrides ?? []).length === 0 ? (
          <Card className="border border-[#E5E5E7]">
            <CardContent className="py-8 text-center text-[#86868B]">
              No active payment overrides. All payments follow their regular schedule.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {(overrides ?? []).map((override: PaymentOverride) => (
              <OverrideCard
                key={override._id}
                override={override}
                contractName={getContractName(override)}
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

function OverrideCard({
  override,
  contractName,
  onDelete,
  formatDate,
}: {
  override: PaymentOverride;
  contractName: string;
  onDelete: (id: string) => void;
  formatDate: (d: string) => string;
}) {
  const isCustomer = override.overrideType === 'customer';
  const isMove = override.action === 'move';

  return (
    <Card className="border border-[#E5E5E7] hover:border-[#007AFF]/20 transition-colors">
      <CardContent className="py-3 px-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 min-w-0">
            {/* Type Icon */}
            <div
              className={`flex-shrink-0 h-8 w-8 rounded-lg flex items-center justify-center ${
                isCustomer ? 'bg-[#34C759]/10' : 'bg-[#FF9500]/10'
              }`}
            >
              {isCustomer ? (
                <Users className={`h-4 w-4 text-[#34C759]`} />
              ) : (
                <Building2 className={`h-4 w-4 text-[#FF9500]`} />
              )}
            </div>

            {/* Details */}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-[#1D1D1F] truncate">
                  {contractName}
                </span>
                <Badge
                  className={`text-[10px] px-1.5 py-0 ${
                    override.entity === 'YAHSHUA'
                      ? 'bg-[#007AFF]/10 text-[#007AFF]'
                      : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                  }`}
                >
                  {override.entity}
                </Badge>
              </div>
              <div className="flex items-center gap-1.5 mt-0.5 text-xs text-[#86868B]">
                <span>{formatDate(override.originalDate)}</span>
                {isMove && override.newDate ? (
                  <>
                    <ArrowRight className="h-3 w-3 text-[#007AFF]" />
                    <span className="text-[#007AFF] font-medium">
                      {formatDate(override.newDate)}
                    </span>
                  </>
                ) : (
                  <>
                    <ArrowRight className="h-3 w-3 text-[#FF3B30]" />
                    <span className="text-[#FF3B30] font-semibold">SKIPPED</span>
                  </>
                )}
              </div>
              {override.reason && (
                <p className="text-xs text-[#86868B] mt-0.5 truncate max-w-md">
                  {override.reason}
                </p>
              )}
            </div>
          </div>

          {/* Delete */}
          <Button
            variant="ghost"
            size="icon-xs"
            onClick={() => onDelete(override._id)}
            title="Remove override"
          >
            <Trash2 className="h-3.5 w-3.5 text-[#FF3B30]" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
