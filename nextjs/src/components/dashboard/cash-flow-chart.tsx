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

  const chartData = data.map((d) => ({
    date: d.date,
    endingCash: parseFloat(d.endingCash),
    label: format(new Date(d.date + 'T00:00:00Z'), 'MMM dd'),
  }));

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
              formatter={(value) => [formatCurrency(Number(value)), 'Cash Position']}
              labelStyle={{ color: '#0f172a', fontWeight: 600, fontSize: 13 }}
              contentStyle={{
                borderRadius: 10,
                border: '1px solid #e2e8f0',
                boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                fontSize: 13,
                padding: '8px 12px',
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
              dot={{
                r: 3,
                fill: '#2563eb',
                strokeWidth: 0,
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
