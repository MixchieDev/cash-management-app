'use client';

import { useAppStore } from '@/stores/app-store';
import { PageHeader } from '@/components/layout/header';
import { KpiCard } from '@/components/dashboard/kpi-card';
import { CashFlowChart } from '@/components/dashboard/cash-flow-chart';
import { AlertsPanel } from '@/components/dashboard/alerts-panel';
import { TransactionModal } from '@/components/dashboard/transaction-modal';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/currency';
import { calculatePeriodRange } from '@/lib/period-helpers';
import type { Timeframe, RevenueEvent, ExpenseEvent } from '@/lib/types';
import { useProjection } from '@/hooks/use-projections';
import { format } from 'date-fns';
import Link from 'next/link';
import {
  Wallet,
  Calendar,
  Clock,
  Timer,
  Activity,
  TrendingUp,
  FileText,
  Target,
  Loader2,
} from 'lucide-react';

const TIMEFRAME_OPTIONS: { value: Timeframe; label: string }[] = [
  { value: 'daily', label: '60 Days' },
  { value: 'weekly', label: '6 Months' },
  { value: 'monthly', label: '1 Year' },
  { value: 'quarterly', label: '3 Years' },
];

const QUICK_ACTIONS = [
  { href: '/dashboard/scenarios', label: 'Create Scenario', icon: TrendingUp, color: 'from-blue-500 to-blue-600' },
  { href: '/dashboard/scenarios', label: 'Compare Scenarios', icon: Activity, color: 'from-violet-500 to-violet-600' },
  { href: '/dashboard/contracts', label: 'View Contracts', icon: FileText, color: 'from-emerald-500 to-emerald-600' },
  { href: '/dashboard/scenarios', label: 'Strategic Planning', icon: Target, color: 'from-amber-500 to-amber-600' },
];

export default function DashboardPage() {
  const {
    selectedEntity,
    timeframe,
    setTimeframe,
    scenarioType,
    setScenarioType,
    transactionModalOpen,
    transactionModalDate,
    openTransactionModal,
    closeTransactionModal,
  } = useAppStore();

  const { data: projection, isLoading, balanceDate } = useProjection(selectedEntity, timeframe, scenarioType);

  const dataPoints = projection?.dataPoints ?? [];
  const currentCash = dataPoints[0]?.startingCash ?? '0';

  const getProjectionAt = (index: number) =>
    dataPoints[index]?.endingCash ?? '0';

  const modalEvents = (() => {
    if (!transactionModalDate || !projection) {
      return { revenue: [] as RevenueEvent[], expenses: [] as ExpenseEvent[], label: '' };
    }
    const clickedDate = new Date(transactionModalDate);
    const projStart = dataPoints.length > 0 ? new Date(dataPoints[0].date) : clickedDate;
    const { periodStart, periodEnd, periodLabel } = calculatePeriodRange(
      clickedDate, timeframe, projStart
    );
    const startStr = periodStart.toISOString().split('T')[0];
    const endStr = periodEnd.toISOString().split('T')[0];

    return {
      revenue: ((projection.revenueEvents ?? []) as unknown as RevenueEvent[]).filter(
        (e) => e.date >= startStr && e.date <= endStr
      ),
      expenses: ((projection.expenseEvents ?? []) as ExpenseEvent[]).filter(
        (e) => e.date >= startStr && e.date <= endStr
      ),
      label: periodLabel,
    };
  })();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Cash Flow Dashboard"
        subtitle="Strategic cash position overview"
      >
        <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
          {(['optimistic', 'realistic'] as const).map((type) => (
            <button
              key={type}
              onClick={() => setScenarioType(type)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all capitalize ${
                scenarioType === type
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </PageHeader>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <KpiCard
          label={balanceDate ? `Cash as of ${format(new Date(balanceDate + 'T00:00:00Z'), 'MMM dd, yyyy')}` : 'Current Cash'}
          value={formatCurrency(currentCash)}
          icon={<Wallet className="h-4 w-4" />}
        />
        <KpiCard
          label="30-Day"
          value={formatCurrency(getProjectionAt(0))}
          icon={<Calendar className="h-4 w-4" />}
          change={dataPoints[0] ? formatCurrency(
            parseFloat(getProjectionAt(0)) - parseFloat(currentCash)
          ) : undefined}
          changePositive={parseFloat(getProjectionAt(0)) >= parseFloat(currentCash)}
        />
        <KpiCard
          label="60-Day"
          value={formatCurrency(getProjectionAt(1))}
          icon={<Clock className="h-4 w-4" />}
        />
        <KpiCard
          label="90-Day"
          value={formatCurrency(getProjectionAt(2))}
          icon={<Timer className="h-4 w-4" />}
        />
        <KpiCard
          label="Cash Runway"
          value={isLoading ? '...' : (() => {
            const negIdx = dataPoints.findIndex((dp: any) => parseFloat(dp.endingCash) < 0);
            if (negIdx === -1) return `${dataPoints.length}+ periods`;
            return `${negIdx} periods`;
          })()}
          icon={<Activity className="h-4 w-4" />}
          changePositive={!dataPoints.some((dp: any) => parseFloat(dp.endingCash) < 0)}
          change={dataPoints.some((dp: any) => parseFloat(dp.endingCash) < 0) ? 'Goes negative' : 'Healthy'}
        />
      </div>

      {/* Alerts */}
      {dataPoints.length > 0 && <AlertsPanel data={dataPoints} />}

      {/* Chart */}
      <div className="rounded-xl bg-white border border-slate-100 shadow-sm">
        <div className="px-6 pt-5 pb-3 flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-slate-900">Cash Flow Projection</h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Click any point for transaction details
            </p>
          </div>
          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
            {TIMEFRAME_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setTimeframe(opt.value)}
                className={`px-3 py-1.5 text-[11px] font-medium rounded-md transition-all ${
                  timeframe === opt.value
                    ? 'bg-white text-slate-900 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <div className="px-2 pb-4">
          {isLoading ? (
            <div className="h-[380px] flex items-center justify-center">
              <Loader2 className="h-6 w-6 text-slate-300 animate-spin" />
            </div>
          ) : (
            <CashFlowChart
              data={dataPoints}
              onPointClick={openTransactionModal}
            />
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-4 gap-4">
        {QUICK_ACTIONS.map((action) => (
          <Link key={action.label} href={action.href}>
            <div className="group rounded-xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-200 p-4 cursor-pointer">
              <div className={`h-9 w-9 rounded-lg bg-gradient-to-br ${action.color} flex items-center justify-center mb-3 group-hover:scale-105 transition-transform`}>
                <action.icon className="h-4 w-4 text-white" />
              </div>
              <p className="text-[13px] font-medium text-slate-700 group-hover:text-slate-900 transition-colors">
                {action.label}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* Transaction Modal */}
      <TransactionModal
        open={transactionModalOpen}
        onClose={closeTransactionModal}
        periodLabel={modalEvents.label}
        revenueEvents={modalEvents.revenue}
        expenseEvents={modalEvents.expenses}
      />
    </div>
  );
}
