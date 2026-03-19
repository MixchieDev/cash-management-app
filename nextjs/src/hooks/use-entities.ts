'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';
import { useConvexMutation } from './use-convex-mutation';

export function useEntities(): any[] | undefined {
  return useQuery(api.entities.getActive) as any;
}

export function useAllEntities(): any[] | undefined {
  return useQuery(api.entities.list) as any;
}

export function useCreateEntity() {
  return useConvexMutation(api.entities.create);
}

export function useUpdateEntity() {
  return useConvexMutation(api.entities.update);
}

export function useDeleteEntity() {
  return useConvexMutation(api.entities.remove);
}

// All account balances grouped by entity (for account selector)
export function useAccountBalances(): any[] | undefined {
  return useQuery(api.projections.getAllAccountBalances) as any;
}
