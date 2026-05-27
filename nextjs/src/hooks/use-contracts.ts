'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';
import { useConvexMutation } from './use-convex-mutation';

// Convex returns branded Id<T> types. We cast to any[] so components
// can use their own interfaces with plain string _id fields.

// ═══════════════════════════════════════════════════════════════
// Customers
// ═══════════════════════════════════════════════════════════════
export function useCustomers(entity?: string): any[] | undefined {
  const entityArg = entity && entity !== 'Consolidated' ? entity : undefined;
  return useQuery(api.customers.list, { entity: entityArg }) as any;
}

export function useCreateCustomer() {
  return useConvexMutation(api.customers.create);
}

export function useUpdateCustomer() {
  return useConvexMutation(api.customers.update);
}

export function useDeactivateCustomer() {
  return useConvexMutation(api.customers.deactivate);
}

export function useDeleteCustomer() {
  return useConvexMutation(api.customers.remove);
}

// ═══════════════════════════════════════════════════════════════
// Vendors
// ═══════════════════════════════════════════════════════════════
export function useVendors(entity?: string): any[] | undefined {
  const entityArg = entity && entity !== 'Consolidated' ? entity : undefined;
  return useQuery(api.vendors.list, { entity: entityArg }) as any;
}

export function useCreateVendor() {
  return useConvexMutation(api.vendors.create);
}

export function useUpdateVendor() {
  return useConvexMutation(api.vendors.update);
}

export function useDeactivateVendor() {
  return useConvexMutation(api.vendors.deactivate);
}

export function useDeleteVendor() {
  return useConvexMutation(api.vendors.remove);
}

// ═══════════════════════════════════════════════════════════════
// Bank Balances
// ═══════════════════════════════════════════════════════════════
export function useBankBalances(entity?: string): any[] | undefined {
  const entityArg = entity && entity !== 'Consolidated' ? entity : undefined;
  return useQuery(api.bankBalances.list, { entity: entityArg }) as any;
}

export function useCreateBankBalance() {
  return useConvexMutation(api.bankBalances.create);
}

export function useDeleteBankBalance() {
  return useConvexMutation(api.bankBalances.remove);
}

// ═══════════════════════════════════════════════════════════════
// Payment Overrides
// ═══════════════════════════════════════════════════════════════
export function useOverrides(entity?: string): any[] | undefined {
  const entityArg = entity && entity !== 'Consolidated' ? entity : undefined;
  return useQuery(api.overrides.list, { entity: entityArg }) as any;
}

export function useCreateOverride() {
  return useConvexMutation(api.overrides.create);
}

export function useDeleteOverride() {
  return useConvexMutation(api.overrides.remove);
}
