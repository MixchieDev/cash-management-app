'use client';

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { formatCurrency } from '@/lib/currency';
import type { RevenueEvent, ExpenseEvent } from '@/lib/types';
import { ArrowDownLeft, ArrowUpRight, Scale } from 'lucide-react';
import { format } from 'date-fns';

interface TransactionModalProps {
  open: boolean;
  onClose: () => void;
  periodLabel: string;
  revenueEvents: RevenueEvent[];
  expenseEvents: ExpenseEvent[];
}

const PRIORITY_CONFIG: Record<number, { label: string; color: string }> = {
  1: { label: 'P1 - Critical', color: 'text-red-600 bg-red-50' },
  2: { label: 'P2 - Contractual', color: 'text-amber-600 bg-amber-50' },
  3: { label: 'P3 - Medium', color: 'text-blue-600 bg-blue-50' },
  4: { label: 'P4 - Flexible', color: 'text-slate-500 bg-slate-50' },
};

export function TransactionModal({
  open,
  onClose,
  periodLabel,
  revenueEvents,
  expenseEvents,
}: TransactionModalProps) {
  const totalInflows = revenueEvents.reduce(
    (sum, e) => sum + parseFloat(e.amount), 0
  );
  const totalOutflows = expenseEvents.reduce(
    (sum, e) => sum + parseFloat(e.amount), 0
  );
  const netFlow = totalInflows - totalOutflows;

  function formatDate(dateStr: string) {
    try {
      return format(new Date(dateStr + 'T00:00:00Z'), 'MMM dd, yyyy');
    } catch {
      return dateStr;
    }
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen: boolean) => !isOpen && onClose()}>
      <DialogContent className="!w-[95vw] !max-w-[1200px] max-h-[90vh] overflow-y-auto p-0">
        {/* Header */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-slate-100">
          <DialogTitle className="text-lg font-semibold text-slate-900">
            Cash Flow Details
          </DialogTitle>
          <p className="text-sm text-slate-500">{periodLabel}</p>
        </DialogHeader>

        <div className="px-6 py-5 space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl bg-emerald-50 border border-emerald-100 p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-7 w-7 rounded-lg bg-emerald-100 flex items-center justify-center">
                  <ArrowDownLeft className="h-3.5 w-3.5 text-emerald-600" />
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-emerald-600">
                  Inflows
                </span>
              </div>
              <p className="text-xl font-bold text-emerald-700 tabular-nums">
                {formatCurrency(totalInflows)}
              </p>
              <p className="text-[11px] text-emerald-500 mt-1">
                {revenueEvents.length} transaction{revenueEvents.length !== 1 ? 's' : ''}
              </p>
            </div>

            <div className="rounded-xl bg-red-50 border border-red-100 p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-7 w-7 rounded-lg bg-red-100 flex items-center justify-center">
                  <ArrowUpRight className="h-3.5 w-3.5 text-red-600" />
                </div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-red-600">
                  Outflows
                </span>
              </div>
              <p className="text-xl font-bold text-red-700 tabular-nums">
                {formatCurrency(totalOutflows)}
              </p>
              <p className="text-[11px] text-red-500 mt-1">
                {expenseEvents.length} transaction{expenseEvents.length !== 1 ? 's' : ''}
              </p>
            </div>

            <div className={`rounded-xl border p-4 ${
              netFlow >= 0
                ? 'bg-blue-50 border-blue-100'
                : 'bg-amber-50 border-amber-100'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <div className={`h-7 w-7 rounded-lg flex items-center justify-center ${
                  netFlow >= 0 ? 'bg-blue-100' : 'bg-amber-100'
                }`}>
                  <Scale className={`h-3.5 w-3.5 ${netFlow >= 0 ? 'text-blue-600' : 'text-amber-600'}`} />
                </div>
                <span className={`text-[11px] font-semibold uppercase tracking-wider ${
                  netFlow >= 0 ? 'text-blue-600' : 'text-amber-600'
                }`}>
                  Net Flow
                </span>
              </div>
              <p className={`text-xl font-bold tabular-nums ${
                netFlow >= 0 ? 'text-blue-700' : 'text-amber-700'
              }`}>
                {netFlow >= 0 ? '+' : ''}{formatCurrency(netFlow)}
              </p>
              <p className={`text-[11px] mt-1 ${netFlow >= 0 ? 'text-blue-500' : 'text-amber-500'}`}>
                {netFlow >= 0 ? 'Positive cash day' : 'Net cash outflow'}
              </p>
            </div>
          </div>

          {/* Revenue Events */}
          {revenueEvents.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Revenue Inflows ({revenueEvents.length})
                </h3>
              </div>
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50/80">
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[120px]">Date</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500">Customer</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 text-right w-[140px]">Amount</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[100px]">Plan</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[80px]">Entity</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {revenueEvents.map((e, i) => (
                      <TableRow key={i} className="hover:bg-slate-50/50">
                        <TableCell className="text-xs text-slate-500 tabular-nums">
                          {formatDate(e.date)}
                        </TableCell>
                        <TableCell className="text-sm font-medium text-slate-900">
                          {e.companyName}
                        </TableCell>
                        <TableCell className="text-sm text-right font-semibold text-emerald-600 tabular-nums">
                          +{formatCurrency(e.amount)}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="text-[10px] font-medium">
                            {e.paymentPlan}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={`text-[10px] font-medium ${
                              e.entity === 'YAHSHUA'
                                ? 'bg-blue-50 text-blue-600'
                                : 'bg-violet-50 text-violet-600'
                            }`}
                          >
                            {e.entity}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {/* Expense Events */}
          {expenseEvents.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="h-1.5 w-1.5 rounded-full bg-red-500" />
                <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Expense Outflows ({expenseEvents.length})
                </h3>
              </div>
              <div className="rounded-xl border border-slate-200 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50/80">
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[120px]">Date</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500">Vendor</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 text-right w-[140px]">Amount</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[110px]">Category</TableHead>
                      <TableHead className="text-[11px] font-semibold text-slate-500 w-[120px]">Priority</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {expenseEvents.map((e, i) => {
                      const priorityCfg = PRIORITY_CONFIG[e.priority] ?? PRIORITY_CONFIG[4];
                      return (
                        <TableRow key={i} className="hover:bg-slate-50/50">
                          <TableCell className="text-xs text-slate-500 tabular-nums">
                            {formatDate(e.date)}
                          </TableCell>
                          <TableCell className="text-sm font-medium text-slate-900">
                            {e.vendorName}
                          </TableCell>
                          <TableCell className="text-sm text-right font-semibold text-red-500 tabular-nums">
                            -{formatCurrency(e.amount)}
                          </TableCell>
                          <TableCell>
                            <Badge variant="secondary" className="text-[10px] font-medium">
                              {e.category}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-semibold ${priorityCfg.color}`}>
                              {priorityCfg.label}
                            </span>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}

          {revenueEvents.length === 0 && expenseEvents.length === 0 && (
            <div className="text-center py-16">
              <div className="h-12 w-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                <Scale className="h-5 w-5 text-slate-400" />
              </div>
              <p className="text-slate-500 font-medium">No transactions</p>
              <p className="text-sm text-slate-400 mt-1">No cash movements on this date</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
