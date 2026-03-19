/**
 * Permission constants and role templates for access control.
 * Port of auth/permissions.py
 */
import type { PermissionKey, UserRole } from '../types';

export const ALL_PERMISSIONS: { key: PermissionKey; label: string; description: string }[] = [
  { key: 'view_dashboard', label: 'View Dashboard', description: 'View Home dashboard & projections' },
  { key: 'view_contracts', label: 'View Contracts', description: 'View customer/vendor contracts' },
  { key: 'edit_contracts', label: 'Edit Contracts', description: 'Add/edit/deactivate contracts' },
  { key: 'view_scenarios', label: 'View Scenarios', description: 'View saved scenarios' },
  { key: 'edit_scenarios', label: 'Edit Scenarios', description: 'Create/edit/delete scenarios' },
  { key: 'manage_overrides', label: 'Manage Overrides', description: 'Create/delete payment overrides' },
  { key: 'import_data', label: 'Import Data', description: 'Upload CSV data imports' },
  { key: 'manage_settings', label: 'Manage Settings', description: 'Change payment terms & config' },
  { key: 'delete_data', label: 'Delete Data', description: 'Use Danger Zone bulk deletes' },
  { key: 'manage_users', label: 'Manage Users', description: 'Add/edit/delete users & permissions' },
];

export const PERMISSION_KEYS: PermissionKey[] = ALL_PERMISSIONS.map((p) => p.key);

export const ROLE_TEMPLATES: Record<UserRole, PermissionKey[]> = {
  admin: PERMISSION_KEYS,
  editor: [
    'view_dashboard',
    'view_contracts',
    'edit_contracts',
    'view_scenarios',
    'edit_scenarios',
    'manage_overrides',
  ],
  viewer: [
    'view_dashboard',
    'view_contracts',
    'view_scenarios',
  ],
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: 'Admin',
  editor: 'Editor',
  viewer: 'Viewer',
};

export function getDefaultPermissions(role: UserRole): PermissionKey[] {
  return ROLE_TEMPLATES[role] ?? ROLE_TEMPLATES.viewer;
}

export function getPermissionLabel(key: PermissionKey): string {
  const perm = ALL_PERMISSIONS.find((p) => p.key === key);
  return perm?.label ?? key;
}

export function hasPermission(userPermissions: PermissionKey[], required: PermissionKey): boolean {
  return userPermissions.includes(required);
}
