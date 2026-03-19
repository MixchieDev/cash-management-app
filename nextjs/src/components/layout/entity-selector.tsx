'use client';

import { useAppStore } from '@/stores/app-store';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { EntityOrConsolidated } from '@/lib/types';

const ENTITIES: { value: EntityOrConsolidated; label: string; color: string }[] = [
  { value: 'Consolidated', label: 'All Entities', color: '#64748b' },
  { value: 'YAHSHUA', label: 'YAHSHUA', color: '#2563eb' },
  { value: 'ABBA', label: 'ABBA', color: '#8b5cf6' },
];

export function EntitySelector() {
  const { selectedEntity, setSelectedEntity } = useAppStore();

  return (
    <Select
      value={selectedEntity}
      onValueChange={(v: string | null) => v && setSelectedEntity(v as EntityOrConsolidated)}
    >
      <SelectTrigger className="w-[160px] h-9 text-[13px] bg-white border-slate-200 shadow-sm">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {ENTITIES.map((e) => (
          <SelectItem key={e.value} value={e.value} className="text-[13px]">
            <span className="flex items-center gap-2">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: e.color }}
              />
              {e.label}
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
