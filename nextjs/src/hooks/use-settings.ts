'use client';

import { useQuery } from 'convex/react';
import { api } from '../../convex/_generated/api';
import { useConvexMutation } from './use-convex-mutation';

export function useSettings(): any[] | undefined {
  return useQuery(api.settings.list) as any;
}

export function useUpdateSetting() {
  return useConvexMutation(api.settings.upsert);
}

export function useAuditLog() {
  return useQuery(api.settings.getAuditLog);
}

// ═══════════════════════════════════════════════════════════════
// Users
// ═══════════════════════════════════════════════════════════════
export function useUsers(): any[] | undefined {
  return useQuery(api.users.list) as any;
}

export function useCreateUser() {
  return useConvexMutation(api.users.create);
}

export function useUpdateUser() {
  return useConvexMutation(api.users.update);
}

export function useResetPassword() {
  return useConvexMutation(api.users.updatePassword);
}

export function useUpdatePermissions() {
  return useConvexMutation(api.users.updatePermissions);
}
