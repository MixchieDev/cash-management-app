'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { formatCurrencyCompact, formatCurrency } from '@/lib/currency';
import type { ProjectionDataPoint } from '@/lib/types';
import { format } from 'date-fns';

interface CashFlowChartProps {
  data: ProjectionDataPoint[];
  onPointClick?: (date: string) => void;
}

export function CashFlowChart({ data, onPointClick }: CashFlowChartProps) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const chartData = data.map((d) => {
    const inflows = parseFloat(d.inflows);
    const outflows = parseFloat(d.outflows);
    const netFlow = inflows - outflows;
    return {
      date: d.date,
      endingCash: parseFloat(d.endingCash),
      inflows,
      outflows,
      netFlow,
      isPositiveDay: netFlow >= 0,
      label: format(new Date(d.date + 'T00:00:00Z'), 'MMM dd'),
    };
  });

  const minCash = chartData.length > 0 ? Math.min(...chartData.map((d) => d.endingCash)) : 0;
  const hasNegative = minCash < 0;
  const hasLowCash = chartData.some((d) => d.endingCash >= 0 && d.endingCash < 500000);

  return (
    <div className="space-y-2">
      <div className="h-[380px] w-full">
        <ResponsiveContainer>
          <LineChart
            data={chartData}
            onMouseMove={(state: any) => {
              if (state?.activeTooltipIndex !== undefined) {
                setActiveIndex(state.activeTooltipIndex);
              }
            }}
            onMouseLeave={() => setActiveIndex(null)}
            onClick={() => {
              if (activeIndex !== null && chartData[activeIndex] && onPointClick) {
                onPointClick(chartData[activeIndex].date);
              }
            }}
          >
            <defs>
              <linearGradient id="cashGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity={0.08} />
                <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={{ stroke: '#e2e8f0' }}
            />
            <YAxis
              tickFormatter={(v) => formatCurrencyCompact(v)}
              tick={{ fontSize: 11, fill: '#94a3b8' }}
              tickLine={false}
              axisLine={false}
              width={80}
            />
            <Tooltip
              content={({ active, payload, label }: any) => {
                if (!active || !payload?.[0]) return null;
                const d = payload[0].payload;
                return (
                  <div className="rounded-lg border border-slate-200 bg-white shadow-lg p-3 text-sm min-w-[200px]">
                    <p className="font-semibold text-slate-900 mb-1.5">{label}</p>
                    <p className="text-slate-600">
                      Cash: <span className="font-semibold">{formatCurrency(d.endingCash)}</span>
                    </p>
                    <div className="border-t border-slate-100 mt-1.5 pt-1.5 space-y-0.5">
                      {d.inflows > 0 && (
                        <p className="text-emerald-600 text-xs">
                          +{formatCurrency(d.inflows)} inflows
                        </p>
                      )}
                      {d.outflows > 0 && (
                        <p className="text-red-500 text-xs">
                          -{formatCurrency(d.outflows)} outflows
                        </p>
                      )}
                      <p className={`text-xs font-semibold ${d.netFlow >= 0 ? 'text-emerald-600' : 'text-red-500'}`}>
                        Net: {d.netFlow >= 0 ? '+' : ''}{formatCurrency(d.netFlow)}
                      </p>
                    </div>
                  </div>
                );
              }}
            />

            {hasNegative && (
              <ReferenceArea
                y1={Math.min(minCash, 0)}
                y2={0}
                fill="#ef4444"
                fillOpacity={0.06}
              />
            )}
            {hasLowCash && (
              <ReferenceArea y1={0} y2={500000} fill="#f59e0b" fillOpacity={0.04} />
            )}

            <Line
              type="monotone"
              dataKey="endingCash"
              stroke="#2563eb"
              strokeWidth={2.5}
              dot={(props: any) => {
                const { cx, cy, payload } = props;
                const color = payload.netFlow >= 0 ? '#10b981' : '#ef4444';
                return (
                  <circle
                    key={`dot-${payload.date}`}
                    cx={cx}
                    cy={cy}
                    r={4}
                    fill={color}
                    stroke="#fff"
                    strokeWidth={1.5}
                  />
                );
              }}
              activeDot={{
                r: 7,
                fill: '#2563eb',
                stroke: '#fff',
                strokeWidth: 3,
                cursor: 'pointer',
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {onPointClick && (
        <p className="text-center text-[11px] text-slate-400">
          Click any point on the chart to view transaction breakdown
        </p>
      )}
    </div>
  );
}
