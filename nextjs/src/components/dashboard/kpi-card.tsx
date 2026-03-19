import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface KpiCardProps {
  label: string;
  value: string;
  change?: string;
  changePositive?: boolean;
  icon?: React.ReactNode;
  className?: string;
}

export function KpiCard({ label, value, change, changePositive, icon, className }: KpiCardProps) {
  return (
    <div className={cn(
      'rounded-xl bg-white border border-slate-100 p-5 shadow-sm hover:shadow-md transition-shadow duration-200',
      className
    )}>
      <div className="flex items-center justify-between">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
          {label}
        </p>
        {icon && <div className="text-slate-300">{icon}</div>}
      </div>
      <p className="text-[22px] font-bold text-slate-900 mt-2 tabular-nums">{value}</p>
      {change && (
        <div className={cn(
          'flex items-center gap-1 mt-2 text-xs font-medium',
          changePositive ? 'text-emerald-600' : 'text-red-500'
        )}>
          {changePositive ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          )}
          {change}
        </div>
      )}
    </div>
  );
}
