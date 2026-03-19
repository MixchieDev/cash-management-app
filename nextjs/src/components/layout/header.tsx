'use client';

import { EntitySelector } from './entity-selector';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  showEntitySelector?: boolean;
  children?: React.ReactNode;
}

export function PageHeader({ title, subtitle, showEntitySelector = true, children }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-8">
      <div>
        <h1 className="text-xl font-semibold text-slate-900 tracking-tight">{title}</h1>
        {subtitle && (
          <p className="text-sm text-slate-500 mt-0.5">{subtitle}</p>
        )}
      </div>
      <div className="flex items-center gap-3">
        {children}
        {showEntitySelector && <EntitySelector />}
      </div>
    </div>
  );
}
