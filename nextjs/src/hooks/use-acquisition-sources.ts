'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';

const DEFAULT_SOURCES = ['RCBC Partner', 'Globe Partner', 'YOWI', 'TAI', 'PEI'];

export function useAcquisitionSources(): string[] {
  const setting = useQuery(api.settings.getByKey, { key: 'acquisition_sources' });

  if (setting?.settingValue) {
    try {
      const parsed = JSON.parse(setting.settingValue);
      if (Array.isArray(parsed) && parsed.length > 0) {
        return parsed;
      }
    } catch {
      // fall through to defaults
    }
  }

  return DEFAULT_SOURCES;
}

export { DEFAULT_SOURCES };
