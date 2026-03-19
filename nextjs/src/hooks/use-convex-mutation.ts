'use client';

import { useState, useCallback } from 'react';
import { useMutation } from 'convex/react';
import type { FunctionReference } from 'convex/server';

/**
 * Wraps Convex useMutation to provide a TanStack Query-like API
 * with .mutateAsync(), .isPending, and .mutate().
 *
 * Args are typed as `any` to avoid branded Convex ID type mismatches
 * when components pass plain string IDs.
 */
export function useConvexMutation<T extends FunctionReference<"mutation", "public", any, any>>(
  mutation: T
) {
  const rawMutate = useMutation(mutation);
  const [isPending, setIsPending] = useState(false);

  const mutateAsync = useCallback(
    async (args?: any): Promise<any> => {
      setIsPending(true);
      try {
        const result = await (rawMutate as any)(args);
        return result;
      } finally {
        setIsPending(false);
      }
    },
    [rawMutate]
  );

  const mutate = useCallback(
    (args?: any) => {
      mutateAsync(args).catch(() => {});
    },
    [mutateAsync]
  );

  return { mutateAsync, mutate, isPending };
}
