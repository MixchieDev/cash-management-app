'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { formatCurrency, formatCurrencyCompact } from '@/lib/currency';
import { useProjection } from '@/hooks/use-projections';
import { useAppStore } from '@/stores/app-store';

const MILESTONES = [50, 75, 100, 150, 200, 250]; // in millions

export function StrategicPlanning() {
  const { selectedEntity, scenarioType } = useAppStore();
  const { data: projection } = useProjection(selectedEntity, 'monthly', scenarioType);

  // Hiring calculator state
  const [calcEmployees, setCalcEmployees] = useState(10);
  const [calcSalary, setCalcSalary] = useState(50000);

  // Revenue target state
  const [targetRevenue, setTargetRevenue] = useState(250000000);
  const [revenuePerClient, setRevenuePerClient] = useState(100000);

  // Calculate current metrics from projection
  const dataPoints = projection?.dataPoints ?? [];
  const currentCash = dataPoints.length > 0 ? parseFloat(dataPoints[0].startingCash) : 0;
  const totalMonthlyInflows = dataPoints.length > 0 ? parseFloat(dataPoints[0].inflows) : 0;
  const totalMonthlyOutflows = dataPoints.length > 0 ? parseFloat(dataPoints[0].outflows) : 0;
  const annualRevenue = totalMonthlyInflows * 12;

  const monthlyPayrollImpact = calcEmployees * calcSalary;
  const annualPayrollImpact = monthlyPayrollImpact * 12;
  const monthlyBurn = totalMonthlyOutflows + monthlyPayrollImpact;
  const canAfford = totalMonthlyInflows > monthlyBurn;

  const revenueGap = targetRevenue - annualRevenue;
  const additionalMRRNeeded = revenueGap > 0 ? revenueGap / 12 : 0;

  return (
    <div className="space-y-6">
      {/* Path to ₱250M */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Path to ₱250M Revenue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-6 mb-6">
            <div className="text-center">
              <p className="text-xs text-[#86868B] uppercase tracking-wider">Current Annual Revenue</p>
              <p className="text-2xl font-semibold text-[#1D1D1F] mt-1">
                {formatCurrencyCompact(annualRevenue)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-[#86868B] uppercase tracking-wider">Target</p>
              <p className="text-2xl font-semibold text-[#007AFF] mt-1">₱250.00M</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-[#86868B] uppercase tracking-wider">Gap</p>
              <p className="text-2xl font-semibold text-[#FF9500] mt-1">
                {formatCurrencyCompact(Math.max(0, 250000000 - annualRevenue))}
              </p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="w-full bg-[#E5E5E7] rounded-full h-3">
            <div
              className="bg-[#007AFF] h-3 rounded-full transition-all"
              style={{ width: `${Math.min(100, (annualRevenue / 250000000) * 100)}%` }}
            />
          </div>
          <p className="text-xs text-[#86868B] mt-1 text-right">
            {((annualRevenue / 250000000) * 100).toFixed(1)}% achieved
          </p>

          <Separator className="my-6" />

          {/* Milestones */}
          <h3 className="text-sm font-medium text-[#1D1D1F] mb-3">Growth Milestones</h3>
          <div className="grid grid-cols-6 gap-3">
            {MILESTONES.map((m) => {
              const target = m * 1000000;
              const achieved = annualRevenue >= target;
              const gap = target - annualRevenue;
              return (
                <div
                  key={m}
                  className={`rounded-xl p-3 text-center ${
                    achieved ? 'bg-[#34C759]/10' : 'bg-[#F5F5F7]'
                  }`}
                >
                  <p className="text-sm font-semibold">₱{m}M</p>
                  {achieved ? (
                    <p className="text-xs text-[#34C759] mt-1">Achieved</p>
                  ) : (
                    <p className="text-xs text-[#86868B] mt-1">
                      Gap: {formatCurrencyCompact(gap)}
                    </p>
                  )}
                  <div className="w-full bg-[#E5E5E7] rounded-full h-1.5 mt-2">
                    <div
                      className={`h-1.5 rounded-full ${achieved ? 'bg-[#34C759]' : 'bg-[#007AFF]'}`}
                      style={{ width: `${Math.min(100, (annualRevenue / target) * 100)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-6">
        {/* Hiring Affordability Calculator */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Hiring Affordability Calculator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Number of Employees</Label>
                <Input type="number" min={1} max={100} value={calcEmployees}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCalcEmployees(Number(e.target.value))} />
              </div>
              <div>
                <Label>Salary per Employee</Label>
                <Input type="number" min={20000} value={calcSalary}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCalcSalary(Number(e.target.value))} />
              </div>
            </div>

            <Separator />

            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Monthly Payroll</span>
                <span className="font-medium text-[#FF3B30]">{formatCurrency(monthlyPayrollImpact)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Annual Cost</span>
                <span className="font-medium text-[#FF3B30]">{formatCurrency(annualPayrollImpact)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Current Monthly Revenue</span>
                <span className="font-medium text-[#34C759]">{formatCurrency(totalMonthlyInflows)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Monthly Burn (with hire)</span>
                <span className="font-medium">{formatCurrency(monthlyBurn)}</span>
              </div>
            </div>

            <div className={`rounded-xl p-4 text-center ${canAfford ? 'bg-[#34C759]/10' : 'bg-[#FF3B30]/10'}`}>
              <p className={`text-sm font-semibold ${canAfford ? 'text-[#34C759]' : 'text-[#FF3B30]'}`}>
                {canAfford
                  ? 'Affordable - Revenue covers expenses + new hires'
                  : `Not affordable - Need ${formatCurrency(monthlyBurn - totalMonthlyInflows)} more monthly revenue`
                }
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Revenue Target Calculator */}
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="text-base">Revenue Target Calculator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Target Annual Revenue</Label>
                <Input type="number" min={50000000} step={10000000} value={targetRevenue}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTargetRevenue(Number(e.target.value))} />
                <p className="text-xs text-[#86868B] mt-1">{formatCurrencyCompact(targetRevenue)}</p>
              </div>
              <div>
                <Label>Avg. Revenue per Client</Label>
                <Input type="number" min={10000} step={10000} value={revenuePerClient}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setRevenuePerClient(Number(e.target.value))} />
                <p className="text-xs text-[#86868B] mt-1">{formatCurrency(revenuePerClient)}/mo per client</p>
              </div>
            </div>

            <Separator />

            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Current Annual Revenue</span>
                <span className="font-medium">{formatCurrencyCompact(annualRevenue)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Revenue Gap</span>
                <span className="font-medium text-[#FF9500]">
                  {revenueGap > 0 ? formatCurrencyCompact(revenueGap) : 'Target reached!'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-[#86868B]">Additional MRR Needed</span>
                <span className="font-medium">{formatCurrency(additionalMRRNeeded)}</span>
              </div>
            </div>

            {revenueGap > 0 && (
              <div className="rounded-xl bg-blue-50 border border-blue-100 p-4">
                <p className="text-xs text-slate-500 mb-1">To reach {formatCurrencyCompact(targetRevenue)}</p>
                <p className="text-sm font-medium text-slate-900">
                  You need {formatCurrency(additionalMRRNeeded)} additional monthly recurring revenue.
                </p>
                {revenuePerClient > 0 && (
                  <p className="text-xs text-slate-500 mt-2">
                    At {formatCurrency(revenuePerClient)}/client, that&apos;s approximately{' '}
                    <span className="font-semibold text-blue-600">
                      {Math.ceil(additionalMRRNeeded / revenuePerClient)} new clients
                    </span>
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
