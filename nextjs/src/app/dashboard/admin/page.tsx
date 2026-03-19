'use client';

import { useState } from 'react';
import { PageHeader } from '@/components/layout/header';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { hash } from 'bcryptjs';
import {
  ALL_PERMISSIONS,
  ROLE_LABELS,
  getDefaultPermissions,
} from '@/lib/auth/permissions';
import type { UserRole, PermissionKey } from '@/lib/types';
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useResetPassword,
  useUpdatePermissions,
} from '@/hooks/use-settings';
import { toast } from 'sonner';

interface UserRecord {
  _id: string;
  _creationTime: number;
  username: string;
  name: string;
  role: string;
  isActive: boolean;
  permissions: string[];
}

export default function AdminPage() {
  const usersData = useUsers();
  const users = usersData ?? [];
  const isLoading = usersData === undefined;
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const resetPassword = useResetPassword();
  const updatePermissions = useUpdatePermissions();

  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);

  // Add form
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [newName, setNewName] = useState('');
  const [newRole, setNewRole] = useState<UserRole>('viewer');

  // Edit form
  const [editName, setEditName] = useState('');
  const [editRole, setEditRole] = useState<UserRole>('viewer');
  const [editPerms, setEditPerms] = useState<string[]>([]);

  // Password form
  const [resetPw, setResetPw] = useState('');

  const selectedUser = (users as UserRecord[]).find((u) => u._id === selectedUserId);

  function openEdit(user: UserRecord) {
    setSelectedUserId(user._id);
    setEditName(user.name);
    setEditRole(user.role as UserRole);
    setEditPerms(user.permissions ?? getDefaultPermissions(user.role as UserRole));
    setShowEditDialog(true);
  }

  async function handleCreate() {
    if (!newUsername || !newPassword || !newName) {
      toast.error('Fill all required fields');
      return;
    }
    try {
      const passwordHash = await hash(newPassword, 10);
      await createUser.mutateAsync({
        username: newUsername,
        passwordHash,
        name: newName,
        role: newRole,
        permissions: getDefaultPermissions(newRole),
      });
      toast.success(`User ${newUsername} created`);
      setShowAddDialog(false);
      setNewUsername(''); setNewPassword(''); setNewName('');
    } catch {
      toast.error('Failed to create user');
    }
  }

  async function handleUpdate() {
    if (!selectedUserId) return;
    try {
      await updateUser.mutateAsync({ id: selectedUserId as any, name: editName, role: editRole });
      await updatePermissions.mutateAsync({ id: selectedUserId as any, permissions: editPerms });
      toast.success('User updated');
      setShowEditDialog(false);
    } catch {
      toast.error('Failed to update user');
    }
  }

  async function handleResetPassword() {
    if (!selectedUserId || !resetPw) return;
    try {
      const hashedPw = await hash(resetPw, 10);
      await resetPassword.mutateAsync({ id: selectedUserId as any, passwordHash: hashedPw });
      toast.success('Password reset');
      setShowPasswordDialog(false);
      setResetPw('');
    } catch {
      toast.error('Failed to reset password');
    }
  }

  function togglePermission(key: string) {
    setEditPerms((prev) =>
      prev.includes(key) ? prev.filter((p) => p !== key) : [...prev, key]
    );
  }

  function applyRoleDefaults() {
    setEditPerms(getDefaultPermissions(editRole));
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="User Administration"
        subtitle="Manage users, roles, and permissions"
        showEntitySelector={false}
      >
        <Button onClick={() => setShowAddDialog(true)} className="bg-[#007AFF]">
          Add User
        </Button>
      </PageHeader>

      {/* Users Table */}
      <Card className="border-0 shadow-sm">
        <CardContent className="pt-6">
          {isLoading ? (
            <p className="text-center text-[#86868B] py-8">Loading users...</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(users as UserRecord[]).map((user) => (
                  <TableRow key={user._id}>
                    <TableCell className="font-medium">@{user.username}</TableCell>
                    <TableCell>{user.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className="capitalize text-xs">
                        {ROLE_LABELS[user.role as UserRole] ?? user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={user.isActive ? 'default' : 'secondary'}
                        className={`text-xs ${user.isActive ? 'bg-[#34C759]' : ''}`}
                      >
                        {user.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-[#86868B]">
                      {user._creationTime ? new Date(user._creationTime).toLocaleDateString() : '—'}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex gap-1 justify-end">
                        <Button size="sm" variant="ghost" onClick={() => openEdit(user)}>
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            setSelectedUserId(user._id);
                            setShowPasswordDialog(true);
                          }}
                        >
                          Reset PW
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className={user.isActive ? 'text-[#FF3B30]' : 'text-[#34C759]'}
                          onClick={async () => {
                            try {
                              await updateUser.mutateAsync({
                                id: user._id as any,
                                isActive: !user.isActive,
                              });
                              toast.success(user.isActive ? 'User deactivated' : 'User reactivated');
                            } catch {
                              toast.error('Failed to update user');
                            }
                          }}
                        >
                          {user.isActive ? 'Deactivate' : 'Reactivate'}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Role Reference */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <CardTitle className="text-base">Role & Permission Reference</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Permission</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-center">Admin</TableHead>
                <TableHead className="text-center">Editor</TableHead>
                <TableHead className="text-center">Viewer</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ALL_PERMISSIONS.map((p) => (
                <TableRow key={p.key}>
                  <TableCell className="font-medium text-xs">{p.label}</TableCell>
                  <TableCell className="text-xs text-[#86868B]">{p.description}</TableCell>
                  <TableCell className="text-center">
                    {getDefaultPermissions('admin').includes(p.key) ? '✓' : '—'}
                  </TableCell>
                  <TableCell className="text-center">
                    {getDefaultPermissions('editor').includes(p.key) ? '✓' : '—'}
                  </TableCell>
                  <TableCell className="text-center">
                    {getDefaultPermissions('viewer').includes(p.key) ? '✓' : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Add User Dialog */}
      <Dialog open={showAddDialog} onOpenChange={(open: boolean) => setShowAddDialog(open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Username</Label>
              <Input value={newUsername} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewUsername(e.target.value)} placeholder="username" />
            </div>
            <div>
              <Label>Password</Label>
              <Input type="password" value={newPassword} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewPassword(e.target.value)} />
            </div>
            <div>
              <Label>Full Name</Label>
              <Input value={newName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNewName(e.target.value)} />
            </div>
            <div>
              <Label>Role</Label>
              <Select value={newRole} onValueChange={(v: string | null) => v && setNewRole(v as UserRole)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-[#86868B] mt-1">
                Default permissions will be applied based on role.
              </p>
            </div>
            <Button onClick={handleCreate} className="w-full bg-[#007AFF]"
              disabled={createUser.isPending}>
              {createUser.isPending ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={showEditDialog} onOpenChange={(open: boolean) => setShowEditDialog(open)}>
        <DialogContent className="max-w-lg max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit User: @{selectedUser?.username}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Full Name</Label>
              <Input value={editName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditName(e.target.value)} />
            </div>
            <div>
              <Label>Role Template</Label>
              <Select value={editRole} onValueChange={(v: string | null) => v && setEditRole(v as UserRole)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                  <SelectItem value="viewer">Viewer</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="ghost" size="sm" className="mt-1 text-xs text-[#007AFF]"
                onClick={applyRoleDefaults}>
                Apply role defaults
              </Button>
            </div>

            <Separator />

            <div>
              <Label className="mb-2 block">Permissions</Label>
              <div className="grid grid-cols-2 gap-2">
                {ALL_PERMISSIONS.map((p) => (
                  <div key={p.key} className="flex items-center gap-2">
                    <Checkbox
                      checked={editPerms.includes(p.key)}
                      onCheckedChange={() => togglePermission(p.key)}
                    />
                    <span className="text-xs">{p.label}</span>
                  </div>
                ))}
              </div>
            </div>

            <Button onClick={handleUpdate} className="w-full bg-[#007AFF]"
              disabled={updateUser.isPending}>
              {updateUser.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={showPasswordDialog} onOpenChange={(open: boolean) => setShowPasswordDialog(open)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reset Password: @{selectedUser?.username}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>New Password</Label>
              <Input type="password" value={resetPw}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setResetPw(e.target.value)} />
            </div>
            <Button onClick={handleResetPassword} className="w-full bg-[#007AFF]"
              disabled={resetPassword.isPending}>
              {resetPassword.isPending ? 'Resetting...' : 'Reset Password'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
