'use client';

import type { ProjectionDataPoint } from '@/lib/types';
import { formatCurrency } from '@/lib/currency';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

interface AlertsPanelProps {
  data: ProjectionDataPoint[];
}

export function AlertsPanel({ data }: AlertsPanelProps) {
  const hasNegative = data.some((d) => parseFloat(d.endingCash) < 0);
  const hasLowCash = data.some(
    (d) => parseFloat(d.endingCash) >= 0 && parseFloat(d.endingCash) < 500000
  );

  if (!hasNegative && !hasLowCash) {
    return (
      <div className="flex items-center gap-3 rounded-lg bg-emerald-50 border border-emerald-100 px-4 py-3">
        <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
        <p className="text-sm font-medium text-emerald-700">
          All clear — no cash alerts in the projection period
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {hasNegative && (
        <div className="flex items-start gap-3 rounded-lg bg-red-50 border border-red-100 px-4 py-3">
          <XCircle className="h-4 w-4 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-700">
              Cash crunch: Negative balance projected
            </p>
            {data
              .filter((d) => parseFloat(d.endingCash) < 0)
              .slice(0, 1)
              .map((d) => (
                <p key={d.date} className="text-xs text-red-500 mt-0.5">
                  First on {d.date}: {formatCurrency(d.endingCash)}
                </p>
              ))}
          </div>
        </div>
      )}
      {hasLowCash && !hasNegative && (
        <div className="flex items-center gap-3 rounded-lg bg-amber-50 border border-amber-100 px-4 py-3">
          <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
          <p className="text-sm font-medium text-amber-700">
            Low cash: Balance drops below {formatCurrency(500000)}
          </p>
        </div>
      )}
    </div>
  );
}
