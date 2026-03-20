'use client';

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/layout/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency } from '@/lib/currency';
import { useSettings, useUpdateSetting, useAuditLog } from '@/hooks/use-settings';
import { useAllEntities, useCreateEntity, useUpdateEntity, useDeleteEntity } from '@/hooks/use-entities';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Download } from 'lucide-react';
import { downloadTemplate } from '@/lib/import-templates';

export default function SettingsPage() {
  const settings = useSettings() ?? [];
  const updateSetting = useUpdateSetting();
  const auditLog = useAuditLog() ?? [];
  const allEntities = useAllEntities() ?? [];
  const createEntity = useCreateEntity();
  const updateEntity = useUpdateEntity();
  const deleteEntity = useDeleteEntity();

  // Entity form state
  const [entityDialogOpen, setEntityDialogOpen] = useState(false);
  const [editingEntity, setEditingEntity] = useState<any>(null);
  const [entityForm, setEntityForm] = useState({ shortCode: '', fullName: '', color: '#2563eb', displayOrder: 0 });

  // Payment terms state
  const [delayDays, setDelayDays] = useState(10);
  const [warningThreshold, setWarningThreshold] = useState(500000);
  const [criticalThreshold, setCriticalThreshold] = useState(0);

  // Sync from saved settings when loaded
  useEffect(() => {
    if (settings.length > 0) {
      const find = (key: string) => settings.find((s: any) => s.settingKey === key);
      const delay = find('realistic_delay_days');
      const warn = find('warning_threshold');
      const crit = find('critical_threshold');
      if (delay) setDelayDays(Number(delay.settingValue));
      if (warn) setWarningThreshold(Number(warn.settingValue));
      if (crit) setCriticalThreshold(Number(crit.settingValue));
    }
  }, [settings]);

  async function savePaymentTerms() {
    try {
      await updateSetting.mutateAsync({
        key: 'realistic_delay_days',
        value: String(delayDays),
      });
      toast.success('Payment terms updated');
    } catch {
      toast.error('Failed to update settings');
    }
  }

  async function saveAlertThresholds() {
    try {
      await updateSetting.mutateAsync({
        key: 'warning_threshold',
        value: String(warningThreshold),
      });
      await updateSetting.mutateAsync({
        key: 'critical_threshold',
        value: String(criticalThreshold),
      });
      toast.success('Alert thresholds updated');
    } catch {
      toast.error('Failed to update thresholds');
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Settings"
        subtitle="System configuration and data management"
        showEntitySelector={false}
      />

      <Tabs defaultValue="payment">
        <TabsList>
          <TabsTrigger value="payment">Payment Terms</TabsTrigger>
          <TabsTrigger value="entities">Entities</TabsTrigger>
          <TabsTrigger value="import">Data Import</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="payment">
          <div className="grid grid-cols-2 gap-6">
            {/* Realistic Scenario Settings */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Realistic Scenario Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Late Payment Delay (days)</Label>
                  <Input
                    type="number"
                    min={0}
                    max={60}
                    value={delayDays}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setDelayDays(Number(e.target.value))}
                  />
                  <p className="text-xs text-[#86868B] mt-1">
                    In realistic scenario, payments are assumed to arrive {delayDays} days late.
                  </p>
                </div>

                <div className="rounded-xl bg-[#007AFF]/5 p-3">
                  <p className="text-xs text-[#1D1D1F]">
                    Example: A payment due on the 5th would arrive on the {5 + delayDays}th in realistic projections.
                  </p>
                </div>

                <Button onClick={savePaymentTerms} className="bg-[#007AFF]"
                  disabled={updateSetting.isPending}>
                  Save Payment Terms
                </Button>
              </CardContent>
            </Card>

            {/* Alert Thresholds */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">Alert Thresholds</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Warning Threshold</Label>
                  <Input
                    type="number"
                    min={0}
                    value={warningThreshold}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWarningThreshold(Number(e.target.value))}
                  />
                  <p className="text-xs text-[#86868B] mt-1">
                    Show warning when cash drops below {formatCurrency(warningThreshold)}
                  </p>
                </div>

                <div>
                  <Label>Critical Threshold</Label>
                  <Input
                    type="number"
                    value={criticalThreshold}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCriticalThreshold(Number(e.target.value))}
                  />
                  <p className="text-xs text-[#86868B] mt-1">
                    Show critical alert when cash drops below {formatCurrency(criticalThreshold)}
                  </p>
                </div>

                {/* Preview */}
                <Separator />
                <div className="space-y-2">
                  <div className="rounded-xl border-l-4 border-[#FF9500] bg-[#FF9500]/5 px-3 py-2">
                    <p className="text-xs text-[#FF9500]">Warning: Below {formatCurrency(warningThreshold)}</p>
                  </div>
                  <div className="rounded-xl border-l-4 border-[#FF3B30] bg-[#FF3B30]/5 px-3 py-2">
                    <p className="text-xs text-[#FF3B30]">Critical: Below {formatCurrency(criticalThreshold)}</p>
                  </div>
                </div>

                <Button onClick={saveAlertThresholds} className="bg-[#007AFF]"
                  disabled={updateSetting.isPending}>
                  Save Alert Thresholds
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="entities">
          <Card className="border-0 shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-sm font-semibold">Entity Management</CardTitle>
              <Button
                size="sm"
                className="bg-blue-600 hover:bg-blue-700"
                onClick={() => {
                  setEditingEntity(null);
                  setEntityForm({ shortCode: '', fullName: '', color: '#2563eb', displayOrder: 0 });
                  setEntityDialogOpen(true);
                }}
              >
                Add Entity
              </Button>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {allEntities.map((entity: any) => (
                  <div
                    key={entity._id}
                    className={`flex items-center gap-4 rounded-xl border p-4 ${
                      entity.isActive ? 'border-slate-200' : 'border-slate-100 opacity-50'
                    }`}
                  >
                    <span
                      className="h-4 w-4 rounded-full flex-shrink-0"
                      style={{ backgroundColor: entity.color ?? '#64748b' }}
                    />
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-slate-900">{entity.shortCode}</p>
                      <p className="text-xs text-slate-500">{entity.fullName}</p>
                    </div>
                    <Badge variant="secondary" className={`text-[10px] ${entity.isActive ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-400'}`}>
                      {entity.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs"
                        onClick={() => {
                          setEditingEntity(entity);
                          setEntityForm({
                            shortCode: entity.shortCode,
                            fullName: entity.fullName,
                            color: entity.color ?? '#64748b',
                            displayOrder: entity.displayOrder ?? 0,
                          });
                          setEntityDialogOpen(true);
                        }}
                      >
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className={entity.isActive ? 'text-xs text-red-500' : 'text-xs text-emerald-600'}
                        onClick={async () => {
                          if (entity.isActive) {
                            await deleteEntity.mutateAsync({ id: entity._id });
                            toast.success(`${entity.shortCode} deactivated`);
                          } else {
                            await updateEntity.mutateAsync({ id: entity._id, isActive: true });
                            toast.success(`${entity.shortCode} reactivated`);
                          }
                        }}
                      >
                        {entity.isActive ? 'Deactivate' : 'Reactivate'}
                      </Button>
                    </div>
                  </div>
                ))}
                {allEntities.length === 0 && (
                  <p className="text-center text-slate-400 py-8">No entities configured.</p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Entity Dialog */}
          <Dialog open={entityDialogOpen} onOpenChange={(open: boolean) => setEntityDialogOpen(open)}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{editingEntity ? 'Edit Entity' : 'Add Entity'}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Short Code</Label>
                  <Input
                    value={entityForm.shortCode}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEntityForm({ ...entityForm, shortCode: e.target.value.toUpperCase() })}
                    placeholder="e.g. YAHSHUA"
                    disabled={!!editingEntity}
                  />
                </div>
                <div>
                  <Label>Full Legal Name</Label>
                  <Input
                    value={entityForm.fullName}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEntityForm({ ...entityForm, fullName: e.target.value })}
                    placeholder="e.g. YAHSHUA Outsourcing Worldwide Inc"
                  />
                </div>
                <div>
                  <Label>Color</Label>
                  <div className="flex items-center gap-3">
                    <input
                      type="color"
                      value={entityForm.color}
                      onChange={(e) => setEntityForm({ ...entityForm, color: e.target.value })}
                      className="h-9 w-14 rounded-md border border-slate-200 cursor-pointer"
                    />
                    <Input
                      value={entityForm.color}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEntityForm({ ...entityForm, color: e.target.value })}
                      placeholder="#2563eb"
                      className="flex-1"
                    />
                  </div>
                </div>
                <div>
                  <Label>Display Order</Label>
                  <Input
                    type="number"
                    value={entityForm.displayOrder}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEntityForm({ ...entityForm, displayOrder: Number(e.target.value) })}
                  />
                </div>
                <Button
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  onClick={async () => {
                    if (!entityForm.shortCode || !entityForm.fullName) {
                      toast.error('Fill in short code and full name');
                      return;
                    }
                    try {
                      if (editingEntity) {
                        await updateEntity.mutateAsync({
                          id: editingEntity._id,
                          fullName: entityForm.fullName,
                          color: entityForm.color,
                          displayOrder: entityForm.displayOrder,
                        });
                        toast.success('Entity updated');
                      } else {
                        await createEntity.mutateAsync({
                          shortCode: entityForm.shortCode,
                          fullName: entityForm.fullName,
                          color: entityForm.color,
                          displayOrder: entityForm.displayOrder,
                        });
                        toast.success('Entity created');
                      }
                      setEntityDialogOpen(false);
                    } catch (err: any) {
                      toast.error(err.message ?? 'Failed to save entity');
                    }
                  }}
                >
                  {editingEntity ? 'Update Entity' : 'Create Entity'}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </TabsContent>

        <TabsContent value="import">
          <div className="space-y-6">
            {([
              { label: 'Customer Contracts', key: 'customers' as const },
              { label: 'Vendor Contracts', key: 'vendors' as const },
              { label: 'Bank Balances', key: 'balances' as const },
            ]).map((type) => (
              <Card key={type.key} className="border-0 shadow-sm">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-base">{type.label} CSV Import</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5 text-xs"
                    onClick={() => downloadTemplate(type.key)}
                  >
                    <Download className="h-3 w-3" />
                    Download Template
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Input type="file" accept=".csv" />
                  <p className="text-xs text-[#86868B]">
                    Upload a CSV file with the appropriate columns for {type.label.toLowerCase()}.
                    Download the template above for the expected format.
                  </p>
                  <Button className="bg-[#007AFF]" disabled>Import</Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="audit">
          <div className="space-y-6">
            {/* Current Settings */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Current Settings ({settings.length})</CardTitle>
              </CardHeader>
              <CardContent>
                {settings.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">No settings configured.</p>
                ) : (
                  <div className="rounded-xl border border-slate-200 overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50/80">
                          <TableHead className="text-[11px] font-semibold text-slate-500">Setting</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">Value</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">Category</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">Type</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {settings.map((s: any) => (
                          <TableRow key={s._id}>
                            <TableCell className="text-sm font-medium text-slate-900">{s.settingKey}</TableCell>
                            <TableCell className="text-sm text-slate-700 font-mono max-w-[200px] truncate">{s.settingValue}</TableCell>
                            <TableCell>
                              <Badge variant="secondary" className="text-[10px]">{s.category}</Badge>
                            </TableCell>
                            <TableCell className="text-xs text-slate-400">{s.settingType}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Change History */}
            <Card className="border-0 shadow-sm">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Change History</CardTitle>
              </CardHeader>
              <CardContent>
                {auditLog.length === 0 ? (
                  <p className="text-center text-slate-400 py-8">
                    No changes recorded yet. Changes will appear here when settings are modified.
                  </p>
                ) : (
                  <div className="rounded-xl border border-slate-200 overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-slate-50/80">
                          <TableHead className="text-[11px] font-semibold text-slate-500">Setting</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">Old Value</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">New Value</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">Changed By</TableHead>
                          <TableHead className="text-[11px] font-semibold text-slate-500">When</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {auditLog.map((entry: any) => (
                          <TableRow key={entry._id}>
                            <TableCell className="text-sm font-medium text-slate-900">{entry.settingKey}</TableCell>
                            <TableCell className="text-sm text-slate-400 font-mono max-w-[150px] truncate">
                              {entry.oldValue ?? '—'}
                            </TableCell>
                            <TableCell className="text-sm text-slate-700 font-mono max-w-[150px] truncate">
                              {entry.newValue}
                            </TableCell>
                            <TableCell className="text-xs text-slate-500">{entry.changedBy ?? '—'}</TableCell>
                            <TableCell className="text-xs text-slate-400">
                              {new Date(entry._creationTime).toLocaleString()}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
