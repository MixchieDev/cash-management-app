'use client';

import { useMemo, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { Search, ArrowDownToLine, ArrowUpFromLine, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { formatCurrency } from '@/lib/currency';
import type { RevenueEvent, ExpenseEvent } from '@/lib/types';

interface ProjectionSearchProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  revenueEvents: RevenueEvent[];
  expenseEvents: ExpenseEvent[];
  /** Window the projection currently covers — shown in the empty-results hint. */
  windowLabel?: string;
}

type Match = {
  name: string;
  entity: string;
  kind: 'inflow' | 'outflow';
  events: Array<{
    date: string;
    amount: string;
    label: string; // e.g. "Quarterly", "Software/Tech"
  }>;
  total: number;
};

export function ProjectionSearch({
  open,
  onOpenChange,
  revenueEvents,
  expenseEvents,
  windowLabel,
}: ProjectionSearchProps) {
  const [query, setQuery] = useState('');

  const results = useMemo<Match[]>(() => {
    const q = query.trim().toLowerCase();
    if (q.length === 0) return [];

    // Group revenue events by company name
    const byName = new Map<string, Match>();

    for (const e of revenueEvents) {
      if (!e.companyName.toLowerCase().includes(q)) continue;
      const key = `inflow::${e.entity}::${e.companyName}`;
      const existing = byName.get(key);
      const event = {
        date: e.date,
        amount: e.amount,
        label: e.paymentPlan || (e.eventType === 'adhoc' ? 'Adjustment' : 'Payment'),
      };
      if (existing) {
        existing.events.push(event);
        existing.total += parseFloat(e.amount);
      } else {
        byName.set(key, {
          name: e.companyName,
          entity: e.entity,
          kind: 'inflow',
          events: [event],
          total: parseFloat(e.amount),
        });
      }
    }

    for (const e of expenseEvents) {
      if (!e.vendorName.toLowerCase().includes(q)) continue;
      const key = `outflow::${e.entity}::${e.vendorName}`;
      const existing = byName.get(key);
      const event = {
        date: e.date,
        amount: e.amount,
        label: e.category || 'Expense',
      };
      if (existing) {
        existing.events.push(event);
        existing.total += parseFloat(e.amount);
      } else {
        byName.set(key, {
          name: e.vendorName,
          entity: e.entity,
          kind: 'outflow',
          events: [event],
          total: parseFloat(e.amount),
        });
      }
    }

    // Sort each match's events by date, then sort matches by total descending
    const out = Array.from(byName.values());
    for (const m of out) m.events.sort((a, b) => a.date.localeCompare(b.date));
    out.sort((a, b) => b.total - a.total);
    return out;
  }, [query, revenueEvents, expenseEvents]);

  const totalEvents = results.reduce((sum, m) => sum + m.events.length, 0);

  function formatDate(iso: string): string {
    return format(new Date(iso + 'T00:00:00Z'), 'MMM dd, yyyy');
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Search Projection</DialogTitle>
          <DialogDescription>
            Find all projected events for a customer or vendor. Searches within
            the current dashboard view {windowLabel ? `(${windowLabel})` : ''}.
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#86868B]" />
          <Input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a name — e.g. Del Monte, AWS, BIR…"
            className="pl-9"
          />
        </div>

        <div className="flex-1 overflow-y-auto -mx-6 px-6">
          {query.trim().length === 0 ? (
            <div className="py-12 text-center text-[#86868B]">
              <Search className="h-6 w-6 mx-auto mb-2 opacity-40" />
              <p className="text-sm">Start typing to search projected events.</p>
              <p className="text-xs mt-1">
                Searches customer/vendor names across all events in the current view.
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="py-12 text-center text-[#86868B]">
              <p className="text-sm">No matches for &ldquo;{query}&rdquo;.</p>
              <p className="text-xs mt-1">
                Try a shorter or different term. If the contract recurs further out,
                switch the dashboard to a longer timeframe.
              </p>
            </div>
          ) : (
            <>
              <p className="text-xs text-[#86868B] mb-3">
                {totalEvents} event{totalEvents === 1 ? '' : 's'} across{' '}
                {results.length} {results.length === 1 ? 'contract' : 'contracts'}
              </p>
              <div className="space-y-3 pb-2">
                {results.map((match, i) => (
                  <Card key={i} className="border border-[#E5E5E7]">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2 min-w-0">
                          <div
                            className={`flex-shrink-0 h-7 w-7 rounded-lg flex items-center justify-center ${
                              match.kind === 'inflow'
                                ? 'bg-[#34C759]/10'
                                : 'bg-[#FF3B30]/10'
                            }`}
                          >
                            {match.kind === 'inflow' ? (
                              <ArrowDownToLine className="h-3.5 w-3.5 text-[#34C759]" />
                            ) : (
                              <ArrowUpFromLine className="h-3.5 w-3.5 text-[#FF3B30]" />
                            )}
                          </div>
                          <span className="font-medium text-sm text-[#1D1D1F] truncate">
                            {match.name}
                          </span>
                          <Badge
                            className={`text-[10px] px-1.5 py-0 ${
                              match.entity === 'YAHSHUA'
                                ? 'bg-[#007AFF]/10 text-[#007AFF]'
                                : 'bg-[#AF52DE]/10 text-[#AF52DE]'
                            }`}
                          >
                            {match.entity}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <div
                            className={`text-sm font-semibold ${
                              match.kind === 'inflow' ? 'text-[#34C759]' : 'text-[#FF3B30]'
                            }`}
                          >
                            {match.kind === 'inflow' ? '+' : '−'}
                            {formatCurrency(match.total).replace('-', '')}
                          </div>
                          <div className="text-[10px] text-[#86868B]">
                            total across {match.events.length} event{match.events.length === 1 ? '' : 's'}
                          </div>
                        </div>
                      </div>

                      <div className="space-y-1.5 pl-9">
                        {match.events.map((ev, j) => (
                          <div
                            key={j}
                            className="flex items-center justify-between text-xs"
                          >
                            <div className="flex items-center gap-2 text-[#86868B]">
                              <Calendar className="h-3 w-3" />
                              <span>{formatDate(ev.date)}</span>
                              {ev.label && (
                                <Badge className="text-[9px] px-1.5 py-0 bg-[#86868B]/10 text-[#86868B]">
                                  {ev.label}
                                </Badge>
                              )}
                            </div>
                            <span
                              className={`font-medium ${
                                match.kind === 'inflow' ? 'text-[#34C759]' : 'text-[#FF3B30]'
                              }`}
                            >
                              {match.kind === 'inflow' ? '+' : '−'}
                              {formatCurrency(ev.amount).replace('-', '')}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
