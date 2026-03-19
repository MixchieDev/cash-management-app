'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';
import { useConvexMutation } from './use-convex-mutation';
import type { Id } from '../../convex/_generated/dataModel';

export function useScenarios(entity?: string): any[] | undefined {
  const entityArg = entity && entity !== 'Consolidated' ? entity : undefined;
  return useQuery(api.scenarios.list, { entity: entityArg }) as any;
}

export function useScenario(id: string | null) {
  return useQuery(
    api.scenarios.get,
    id ? { id: id as Id<"scenarios"> } : "skip"
  );
}

export function useCreateScenario() {
  return useConvexMutation(api.scenarios.create);
}

export function useDeleteScenario() {
  return useConvexMutation(api.scenarios.remove);
}

/**
 * Stub for running a scenario — the scenario builder component
 * calls this after saving. With Convex, projections are computed
 * client-side via useProjection, so this is a no-op placeholder.
 * The component handles the result display separately.
 */
export function useRunScenario() {
  return {
    mutateAsync: async (_args: { scenarioId: string; timeframe: string; scenarioType: string }) => {
      // With Convex, scenario comparison is done client-side using the engine
      return { baseline: [], scenario: [] };
    },
    isPending: false,
  };
}

export function useCompareScenarios() {
  return {
    mutateAsync: async (_args: { scenarioIds: string[]; entity: string; timeframe: string; scenarioType: string }) => {
      return { baseline: [], scenarios: [] };
    },
    isPending: false,
  };
}
