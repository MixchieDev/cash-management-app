'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { signOut, useSession } from 'next-auth/react';
import {
  LayoutDashboard,
  TrendingUp,
  FileText,
  Settings,
  Shield,
  LogOut,
  ChevronRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

const navItems = [
  { href: '/dashboard', label: 'Home', icon: LayoutDashboard, permission: 'view_dashboard' },
  { href: '/dashboard/scenarios', label: 'Scenarios', icon: TrendingUp, permission: 'view_scenarios' },
  { href: '/dashboard/contracts', label: 'Contracts', icon: FileText, permission: 'view_contracts' },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings, permission: 'manage_settings' },
  { href: '/dashboard/admin', label: 'Admin', icon: Shield, permission: 'manage_users' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: session } = useSession();
  const userPermissions = (session?.user as { permissions?: string[] })?.permissions ?? [];
  const role = (session?.user as { role?: string })?.role;
  const username = (session?.user as { username?: string })?.username;

  return (
    <aside className="flex h-screen w-[260px] flex-col bg-white border-r border-slate-100">
      {/* Logo */}
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-blue-600 to-violet-600 flex items-center justify-center text-base font-bold text-white shadow-sm shadow-blue-600/20">
            ₱
          </div>
          <div>
            <h1 className="text-[15px] font-semibold text-slate-900 leading-tight">Cash Management</h1>
            <p className="text-[11px] text-slate-400 font-medium">JESUS Company</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-0.5">
        <p className="px-3 py-2 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
          Menu
        </p>
        {navItems
          .filter((item) => userPermissions.includes(item.permission))
          .map((item) => {
            const isActive =
              item.href === '/dashboard'
                ? pathname === '/dashboard'
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                  isActive
                    ? 'bg-blue-50 text-blue-600 shadow-sm shadow-blue-100/50'
                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
                )}
              >
                <item.icon className={cn('h-[18px] w-[18px]', isActive ? 'text-blue-600' : 'text-slate-400')} />
                <span className="flex-1">{item.label}</span>
                {isActive && <ChevronRight className="h-3.5 w-3.5 text-blue-400" />}
              </Link>
            );
          })}
      </nav>

      {/* User info */}
      <div className="px-3 pb-4 space-y-2">
        <div className="rounded-lg bg-slate-50 px-3 py-3">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white">
              {session?.user?.name?.charAt(0)?.toUpperCase() ?? '?'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[13px] font-medium text-slate-900 truncate">
                {session?.user?.name}
              </p>
              <p className="text-[11px] text-slate-400">
                {role && <span className="capitalize">{role}</span>}
                {username && <span> &middot; @{username}</span>}
              </p>
            </div>
          </div>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-slate-400 hover:text-red-500 hover:bg-red-50 text-xs h-8"
          onClick={() => signOut({ callbackUrl: '/login' })}
        >
          <LogOut className="mr-2 h-3.5 w-3.5" />
          Sign Out
        </Button>
      </div>
    </aside>
  );
}
