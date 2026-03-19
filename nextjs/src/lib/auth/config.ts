/**
 * NextAuth.js v5 configuration with Credentials provider.
 * Uses Convex httpAction or direct fetch for server-side user lookup.
 */
import NextAuth from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import { compare } from 'bcryptjs';
import { ConvexHttpClient } from 'convex/browser';
import { api } from '../../../convex/_generated/api';
import type { PermissionKey, UserRole } from '../types';

const convex = new ConvexHttpClient(process.env.NEXT_PUBLIC_CONVEX_URL!);

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      name: 'credentials',
      credentials: {
        username: { label: 'Username', type: 'text' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) return null;

        const username = credentials.username as string;
        const password = credentials.password as string;

        // Look up user via Convex query
        const user = await convex.query(api.users.getByUsername, { username });

        if (!user || !user.isActive) return null;

        // Verify password
        const valid = await compare(password, user.passwordHash);
        if (!valid) return null;

        return {
          id: user._id,
          name: user.name,
          email: user.username,
          role: user.role as UserRole,
          permissions: (user.permissions ?? []) as PermissionKey[],
        };
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as { role: UserRole }).role;
        token.permissions = (user as { permissions: PermissionKey[] }).permissions;
        token.username = user.email;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id = token.sub!;
        (session.user as { role: UserRole }).role = token.role as UserRole;
        (session.user as { permissions: PermissionKey[] }).permissions =
          token.permissions as PermissionKey[];
        (session.user as { username: string }).username = token.username as string;
      }
      return session;
    },
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
  },
});
