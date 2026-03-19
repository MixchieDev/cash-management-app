import type { PermissionKey, UserRole } from '@/lib/types';

declare module 'next-auth' {
  interface User {
    role: UserRole;
    permissions: PermissionKey[];
  }

  interface Session {
    user: {
      id: string;
      name: string;
      email: string;
      username: string;
      role: UserRole;
      permissions: PermissionKey[];
    };
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    role: UserRole;
    permissions: PermissionKey[];
    username: string;
  }
}
