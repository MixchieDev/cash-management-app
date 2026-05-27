'use client';

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { useAppStore } from '@/stores/app-store';
import { addDays, format } from 'date-fns';

interface CustomRangePickerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Earliest possible start — usually the latest bank balance date. */
  balanceDate: string | null;
}

export function CustomRangePicker({
  open,
  onOpenChange,
  balanceDate,
}: CustomRangePickerProps) {
  const { customRangeStart, customRangeEnd, setCustomRange, clearCustomRange } =
    useAppStore();

  // Local form state — only commits to the store on Apply.
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [error, setError] = useState('');

  // Seed the form whenever the modal opens.
  useEffect(() => {
    if (!open) return;
    if (customRangeStart && customRangeEnd) {
      setStart(customRangeStart);
      setEnd(customRangeEnd);
    } else if (balanceDate) {
      // Default to "from balance date for the next 90 days"
      setStart(balanceDate);
      setEnd(format(addDays(new Date(balanceDate + 'T00:00:00Z'), 90), 'yyyy-MM-dd'));
    } else {
      const today = format(new Date(), 'yyyy-MM-dd');
      setStart(today);
      setEnd(format(addDays(new Date(), 90), 'yyyy-MM-dd'));
    }
    setError('');
  }, [open, balanceDate, customRangeStart, customRangeEnd]);

  function handleApply() {
    if (!start || !end) {
      setError('Both start and end dates are required.');
      return;
    }
    if (start > end) {
      setError('Start date must be before end date.');
      return;
    }
    setCustomRange(start, end);
    onOpenChange(false);
  }

  function handleClear() {
    clearCustomRange();
    onOpenChange(false);
  }

  const isActive = Boolean(customRangeStart && customRangeEnd);

  // Quick-pick helpers
  function quickPick(offsetDays: number) {
    const anchor = balanceDate
      ? new Date(balanceDate + 'T00:00:00Z')
      : new Date();
    setStart(format(anchor, 'yyyy-MM-dd'));
    setEnd(format(addDays(anchor, offsetDays), 'yyyy-MM-dd'));
    setError('');
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Custom date range</DialogTitle>
          <DialogDescription>
            Show the projection between any two dates. Overrides the timeframe
            preset until cleared.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="range-start">Start</Label>
              <Input
                id="range-start"
                type="date"
                value={start}
                onChange={(e) => {
                  setStart(e.target.value);
                  setError('');
                }}
                min={balanceDate ?? undefined}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="range-end">End</Label>
              <Input
                id="range-end"
                type="date"
                value={end}
                onChange={(e) => {
                  setEnd(e.target.value);
                  setError('');
                }}
                min={start || balanceDate || undefined}
              />
            </div>
          </div>

          {balanceDate && (
            <p className="text-xs text-[#86868B]">
              Balance is dated {format(new Date(balanceDate + 'T00:00:00Z'), 'MMM dd, yyyy')}.
              Start dates earlier than this are clamped — the engine never
              projects from before the latest known cash position.
            </p>
          )}

          <div className="space-y-1.5">
            <Label className="text-xs text-[#86868B]">Quick picks (from balance date)</Label>
            <div className="flex flex-wrap gap-1.5">
              {[
                { label: '30 days', d: 30 },
                { label: '90 days', d: 90 },
                { label: '6 months', d: 180 },
                { label: '1 year', d: 365 },
                { label: '2 years', d: 730 },
              ].map((p) => (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => quickPick(p.d)}
                  className="px-2.5 py-1 text-[11px] rounded-md bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {error && <p className="text-xs text-[#FF3B30]">{error}</p>}
        </div>

        <DialogFooter className="flex sm:justify-between gap-2">
          <Button
            variant="outline"
            type="button"
            onClick={handleClear}
            disabled={!isActive}
          >
            Clear custom range
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              type="button"
              onClick={handleApply}
              className="bg-[#007AFF] text-white hover:bg-[#007AFF]/90"
            >
              Apply
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
