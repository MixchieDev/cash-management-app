'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { formatCurrencyCompact, formatCurrency } from '@/lib/currency';
import { format } from 'date-fns';

interface DataPoint {
  date: string;
  endingCash: string;
}

interface ScenarioLine {
  name: string;
  dataPoints: DataPoint[];
}

interface ComparisonChartProps {
  baseline: DataPoint[];
  scenarios: ScenarioLine[];
}

const SCENARIO_COLORS = ['#2563eb', '#10b981', '#f59e0b'];

export function ComparisonChart({ baseline, scenarios }: ComparisonChartProps) {
  const chartData = baseline.map((bp, i) => {
    const point: Record<string, unknown> = {
      date: bp.date,
      label: format(new Date(bp.date + 'T00:00:00Z'), 'MMM dd'),
      baseline: parseFloat(bp.endingCash),
    };
    scenarios.forEach((s, si) => {
      if (s.dataPoints[i]) {
        point[`scenario_${si}`] = parseFloat(s.dataPoints[i].endingCash);
      }
    });
    return point;
  });

  return (
    <div className="h-[400px] w-full">
      <ResponsiveContainer>
        <LineChart data={chartData}>
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
            formatter={(value, name) => [
              formatCurrency(Number(value)),
              name === 'baseline' ? 'Baseline' : name,
            ]}
            labelStyle={{ color: '#0f172a', fontWeight: 600, fontSize: 13 }}
            contentStyle={{
              borderRadius: 10,
              border: '1px solid #e2e8f0',
              boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
              fontSize: 13,
              padding: '8px 12px',
            }}
          />
          <Legend
            wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
          />

          <Line
            type="monotone"
            dataKey="baseline"
            name="Baseline"
            stroke="#94a3b8"
            strokeWidth={2}
            strokeDasharray="6 3"
            dot={false}
          />

          {scenarios.map((s, i) => (
            <Line
              key={i}
              type="monotone"
              dataKey={`scenario_${i}`}
              name={s.name}
              stroke={SCENARIO_COLORS[i % SCENARIO_COLORS.length]}
              strokeWidth={2.5}
              dot={{ r: 3, fill: SCENARIO_COLORS[i % SCENARIO_COLORS.length], strokeWidth: 0 }}
              activeDot={{ r: 5, fill: SCENARIO_COLORS[i % SCENARIO_COLORS.length], stroke: '#fff', strokeWidth: 2 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
