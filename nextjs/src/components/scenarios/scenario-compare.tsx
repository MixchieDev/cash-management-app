'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { formatCurrency, formatCurrencyCompact } from '@/lib/currency';
import { useScenarios } from '@/hooks/use-scenarios';
import { useAppStore } from '@/stores/app-store';
import { useProjection } from '@/hooks/use-projections';
import { ComparisonChart } from './comparison-chart';
import { ScenarioCalculator, type ScenarioChangeData } from '@/lib/engine/scenario-calculator';
import Decimal from 'decimal.js';
import { toast } from 'sonner';
import {
  Loader2,
  Users,
  Receipt,
  TrendingUp,
  TrendingDown,
  DollarSign,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface ScenarioChange {
  changeType: string;
  startDate: string;
  endDate?: string;
  employees?: number;
  salaryPerEmployee?: number;
  expenseName?: string;
  expenseAmount?: number;
  newClients?: number;
  revenuePerClient?: number;
  investmentAmount?: number;
  lostRevenue?: number;
}

interface ScenarioRecord {
  _id: string;
  _creationTime: number;
  scenarioName: string;
  entity: string;
  description?: string;
  createdBy?: string;
  changes: ScenarioChange[];
}

const CHANGE_TYPE_CONFIG: Record<string, { icon: typeof Users; label: string; color: string }> = {
  hiring: { icon: Users, label: 'Hiring', color: 'text-blue-600 bg-blue-50' },
  expense: { icon: Receipt, label: 'Expense', color: 'text-red-600 bg-red-50' },
  revenue: { icon: TrendingUp, label: 'Revenue', color: 'text-emerald-600 bg-emerald-50' },
  customer_loss: { icon: TrendingDown, label: 'Customer Loss', color: 'text-amber-600 bg-amber-50' },
  investment: { icon: DollarSign, label: 'Investment', color: 'text-violet-600 bg-violet-50' },
};

function describeChange(c: ScenarioChange): string {
  switch (c.changeType) {
    case 'hiring':
      return `Hire ${c.employees} employees @ ${formatCurrency(c.salaryPerEmployee ?? 0)}/mo`;
    case 'expense':
      return `${c.expenseName ?? 'Expense'}: ${formatCurrency(c.expenseAmount ?? 0)}/mo`;
    case 'revenue':
      return `${c.newClients} new clients @ ${formatCurrency(c.revenuePerClient ?? 0)}/mo`;
    case 'customer_loss':
      return `Lose ${formatCurrency(c.lostRevenue ?? 0)}/mo revenue`;
    case 'investment':
      return `One-time investment of ${formatCurrency(c.investmentAmount ?? 0)}`;
    default:
      return c.changeType;
  }
}

function monthlyImpact(c: ScenarioChange): number {
  switch (c.changeType) {
    case 'hiring': return -(c.employees ?? 0) * (c.salaryPerEmployee ?? 0);
    case 'expense': return -(c.expenseAmount ?? 0);
    case 'revenue': return (c.newClients ?? 0) * (c.revenuePerClient ?? 0);
    case 'customer_loss': return -(c.lostRevenue ?? 0);
    case 'investment': return -(c.investmentAmount ?? 0);
    default: return 0;
  }
}

export function ScenarioCompare() {
  const { selectedEntity, scenarioType } = useAppStore();
  const scenariosData = useScenarios(selectedEntity);
  const scenarios = (scenariosData ?? []) as ScenarioRecord[];
  const isLoading = scenariosData === undefined;
  const [selected, setSelected] = useState<string[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [expandedScenario, setExpandedScenario] = useState<string | null>(null);

  const { data: projection, isLoading: projLoading } = useProjection(
    selectedEntity, 'monthly', scenarioType
  );

  function toggleSelection(id: string) {
    if (selected.includes(id)) {
      setSelected(selected.filter((s) => s !== id));
    } else if (selected.length < 3) {
      setSelected([...selected, id]);
    } else {
      toast.error('Maximum 3 scenarios can be compared');
    }
  }

  const comparisonResult = useMemo(() => {
    if (!showResults || !projection || projection.dataPoints.length === 0 || selected.length === 0) {
      return null;
    }

    const calculator = new ScenarioCalculator();

    const baselinePoints = projection.dataPoints.map((dp: any) => ({
      date: new Date(dp.date),
      startingCash: new Decimal(dp.startingCash),
      inflows: new Decimal(dp.inflows),
      outflows: new Decimal(dp.outflows),
      endingCash: new Decimal(dp.endingCash),
      entity: dp.entity,
      timeframe: dp.timeframe,
      scenarioType: dp.scenarioType,
      isNegative: dp.isNegative,
    }));

    const scenarioResults = selected.map((scenarioId) => {
      const scenario = scenarios.find((s) => s._id === scenarioId);
      if (!scenario) return null;

      const changes: ScenarioChangeData[] = scenario.changes.map((c) => ({
        changeType: c.changeType,
        startDate: new Date(c.startDate),
        endDate: c.endDate ? new Date(c.endDate) : null,
        employees: c.employees,
        salaryPerEmployee: c.salaryPerEmployee ? new Decimal(c.salaryPerEmployee) : undefined,
        expenseName: c.expenseName,
        expenseAmount: c.expenseAmount ? new Decimal(c.expenseAmount) : undefined,
        newClients: c.newClients,
        revenuePerClient: c.revenuePerClient ? new Decimal(c.revenuePerClient) : undefined,
        investmentAmount: c.investmentAmount ? new Decimal(c.investmentAmount) : undefined,
        lostRevenue: c.lostRevenue ? new Decimal(c.lostRevenue) : undefined,
      }));

      const resultPoints = calculator.applyScenarioChanges(baselinePoints, changes);
      const totalMonthlyImpact = scenario.changes.reduce((sum, c) => sum + monthlyImpact(c), 0);

      return {
        _id: scenario._id,
        name: scenario.scenarioName,
        entity: scenario.entity,
        changes: scenario.changes,
        totalMonthlyImpact,
        dataPoints: resultPoints.map((dp) => ({
          date: dp.date instanceof Date ? dp.date.toISOString().split('T')[0] : String(dp.date),
          endingCash: dp.endingCash.toFixed(2),
          inflows: dp.inflows.toFixed(2),
          outflows: dp.outflows.toFixed(2),
        })),
      };
    }).filter(Boolean) as {
      _id: string;
      name: string;
      entity: string;
      changes: ScenarioChange[];
      totalMonthlyImpact: number;
      dataPoints: { date: string; endingCash: string; inflows: string; outflows: string }[];
    }[];

    const baseline = projection.dataPoints.map((dp: any) => ({
      date: dp.date,
      endingCash: dp.endingCash,
    }));

    // Calculate baseline totals
    const baselineTotalInflows = projection.dataPoints.reduce(
      (sum: number, dp: any) => sum + parseFloat(dp.inflows), 0
    );
    const baselineTotalOutflows = projection.dataPoints.reduce(
      (sum: number, dp: any) => sum + parseFloat(dp.outflows), 0
    );

    return { baseline, scenarios: scenarioResults, baselineTotalInflows, baselineTotalOutflows };
  }, [showResults, projection, selected, scenarios]);

  function handleCompare() {
    if (selected.length === 0) { toast.error('Select at least one scenario'); return; }
    setShowResults(true);
  }

  const SCENARIO_COLORS = ['#2563eb', '#10b981', '#f59e0b'];

  return (
    <div className="space-y-6">
      <div className="rounded-lg bg-blue-50 border border-blue-100 px-4 py-3">
        <p className="text-sm text-slate-700">
          Select 1-3 saved scenarios to compare their impact against the baseline cash flow projection.
        </p>
      </div>

      {/* Scenario Selection */}
      <div className="space-y-3">
        {isLoading ? (
          <div className="text-center text-slate-400 py-8">
            <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
            Loading scenarios...
          </div>
        ) : scenarios.length === 0 ? (
          <div className="text-center text-slate-400 py-12">
            <p className="font-medium">No saved scenarios</p>
            <p className="text-sm mt-1">Build a scenario first in the Build tab</p>
          </div>
        ) : (
          scenarios.map((s) => {
            const isSelected = selected.includes(s._id);
            const isExpanded = expandedScenario === s._id;
            const totalImpact = s.changes.reduce((sum, c) => sum + monthlyImpact(c), 0);

            return (
              <div
                key={s._id}
                className={`rounded-xl border transition-all ${
                  isSelected
                    ? 'border-blue-200 bg-blue-50/50 shadow-sm'
                    : 'border-slate-200 bg-white hover:border-slate-300'
                }`}
              >
                <div
                  className="flex items-center gap-4 px-4 py-3 cursor-pointer"
                  onClick={() => toggleSelection(s._id)}
                >
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={() => toggleSelection(s._id)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-slate-900">{s.scenarioName}</p>
                      <Badge variant="secondary" className={`text-[10px] ${
                        s.entity === 'YAHSHUA' ? 'bg-blue-50 text-blue-600' :
                        s.entity === 'ABBA' ? 'bg-violet-50 text-violet-600' :
                        'bg-slate-50 text-slate-600'
                      }`}>
                        {s.entity}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-xs text-slate-400">
                        {s.changes.length} change{s.changes.length !== 1 ? 's' : ''}
                      </span>
                      <span className="text-xs text-slate-300">&middot;</span>
                      <span className={`text-xs font-medium ${totalImpact >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                        {totalImpact >= 0 ? '+' : ''}{formatCurrencyCompact(totalImpact)}/mo
                      </span>
                      <span className="text-xs text-slate-300">&middot;</span>
                      <span className="text-xs text-slate-400">
                        {new Date(s._creationTime).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setExpandedScenario(isExpanded ? null : s._id);
                    }}
                    className="p-1 rounded-md hover:bg-slate-100 text-slate-400"
                  >
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </button>
                </div>

                {/* Expanded change details */}
                {isExpanded && (
                  <div className="px-4 pb-3 pt-0">
                    <Separator className="mb-3" />
                    <div className="space-y-2">
                      {s.changes.map((c, i) => {
                        const config = CHANGE_TYPE_CONFIG[c.changeType] ?? CHANGE_TYPE_CONFIG.expense;
                        const Icon = config.icon;
                        const impact = monthlyImpact(c);
                        return (
                          <div key={i} className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2">
                            <div className={`h-7 w-7 rounded-md flex items-center justify-center ${config.color}`}>
                              <Icon className="h-3.5 w-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-medium text-slate-700">{describeChange(c)}</p>
                              <p className="text-[10px] text-slate-400">From {c.startDate}{c.endDate ? ` to ${c.endDate}` : ' onwards'}</p>
                            </div>
                            <span className={`text-xs font-semibold tabular-nums ${impact >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                              {impact >= 0 ? '+' : ''}{formatCurrencyCompact(impact)}/mo
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Compare Button */}
      {scenarios.length > 0 && (
        <div className="flex justify-end">
          <Button
            onClick={handleCompare}
            className="bg-blue-600 hover:bg-blue-700 px-6"
            disabled={selected.length === 0 || projLoading}
          >
            {projLoading ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" /> Loading...</>
            ) : (
              <>Compare {selected.length} Scenario{selected.length !== 1 ? 's' : ''} <ArrowRight className="ml-2 h-3.5 w-3.5" /></>
            )}
          </Button>
        </div>
      )}

      {/* Results */}
      {comparisonResult && comparisonResult.baseline.length > 0 && (
        <>
          <Separator />

          {/* Chart */}
          <Card className="border border-slate-100 shadow-sm">
            <CardHeader>
              <CardTitle className="text-sm font-semibold">
                Cash Flow Projection Comparison
              </CardTitle>
              <p className="text-xs text-slate-400">
                Baseline (dashed) vs {comparisonResult.scenarios.map((s) => s.name).join(', ')}
              </p>
            </CardHeader>
            <CardContent>
              <ComparisonChart
                baseline={comparisonResult.baseline}
                scenarios={comparisonResult.scenarios.map((s) => ({
                  name: s.name,
                  dataPoints: s.dataPoints,
                }))}
              />
            </CardContent>
          </Card>

          {/* Ending Cash Comparison */}
          <div className="grid grid-cols-4 gap-4">
            <Card className="border border-slate-200 shadow-sm">
              <CardContent className="pt-5 pb-4">
                <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Baseline</p>
                <p className="text-xl font-bold text-slate-900 mt-1 tabular-nums">
                  {formatCurrency(comparisonResult.baseline[comparisonResult.baseline.length - 1].endingCash)}
                </p>
                <p className="text-[10px] text-slate-400 mt-1">Ending cash position</p>
              </CardContent>
            </Card>
            {comparisonResult.scenarios.map((s, i) => {
              const scenarioEnd = parseFloat(s.dataPoints[s.dataPoints.length - 1]?.endingCash ?? '0');
              const baselineEnd = parseFloat(comparisonResult.baseline[comparisonResult.baseline.length - 1].endingCash);
              const diff = scenarioEnd - baselineEnd;
              return (
                <Card key={s._id} className="border shadow-sm" style={{ borderColor: SCENARIO_COLORS[i] + '40' }}>
                  <CardContent className="pt-5 pb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full" style={{ backgroundColor: SCENARIO_COLORS[i] }} />
                      <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: SCENARIO_COLORS[i] }}>
                        {s.name}
                      </p>
                    </div>
                    <p className="text-xl font-bold text-slate-900 mt-1 tabular-nums">
                      {formatCurrency(scenarioEnd)}
                    </p>
                    <p className={`text-xs font-medium mt-1 ${diff >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {diff >= 0 ? '+' : ''}{formatCurrency(diff)} vs baseline
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Detailed Scenario Breakdowns */}
          {comparisonResult.scenarios.map((s, i) => (
            <Card key={s._id} className="border border-slate-100 shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-3">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: SCENARIO_COLORS[i] }} />
                  <CardTitle className="text-sm font-semibold">{s.name}</CardTitle>
                  <Badge variant="secondary" className="text-[10px]">{s.entity}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Monthly Net Impact</p>
                    <p className={`text-lg font-bold mt-1 tabular-nums ${s.totalMonthlyImpact >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {s.totalMonthlyImpact >= 0 ? '+' : ''}{formatCurrency(s.totalMonthlyImpact)}/mo
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Annual Impact</p>
                    <p className={`text-lg font-bold mt-1 tabular-nums ${s.totalMonthlyImpact >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                      {s.totalMonthlyImpact >= 0 ? '+' : ''}{formatCurrency(s.totalMonthlyImpact * 12)}/yr
                    </p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Changes Applied</p>
                    <p className="text-lg font-bold text-slate-900 mt-1">{s.changes.length}</p>
                  </div>
                </div>

                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Change Details</p>
                <div className="space-y-2">
                  {s.changes.map((c, ci) => {
                    const config = CHANGE_TYPE_CONFIG[c.changeType] ?? CHANGE_TYPE_CONFIG.expense;
                    const Icon = config.icon;
                    const impact = monthlyImpact(c);
                    return (
                      <div key={ci} className="flex items-center gap-3 rounded-lg border border-slate-100 px-4 py-3">
                        <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${config.color}`}>
                          <Icon className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium text-slate-900">{describeChange(c)}</p>
                            <Badge variant="secondary" className={`text-[9px] ${config.color}`}>
                              {config.label}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-400 mt-0.5">
                            Starting {c.startDate}{c.endDate ? ` until ${c.endDate}` : ' (ongoing)'}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className={`text-sm font-bold tabular-nums ${impact >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                            {impact >= 0 ? '+' : '-'}{formatCurrency(Math.abs(impact))}
                          </p>
                          <p className="text-[10px] text-slate-400">per month</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </>
      )}
    </div>
  );
}
