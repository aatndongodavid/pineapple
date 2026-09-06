// frontend/src/components/layout/AdminSidebar.tsx

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ShieldCheck,
  Vote,
  Flag,
  CreditCard,
  Building2,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTenantStore } from '@/lib/store/tenantStore';

const adminNavItems = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/identity', label: 'Identity & Certifications', icon: ShieldCheck },
  { to: '/admin/democracy', label: 'Democracy Control', icon: Vote },
  { to: '/admin/trust-safety', label: 'Trust & Safety', icon: Flag },
  { to: '/admin/monetization', label: 'Monetization', icon: CreditCard },
];

export const AdminSidebar: React.FC = () => {
  const { campusName } = useTenantStore();

  return (
    <aside className="hidden md:flex flex-col w-72 h-screen bg-gray-900 text-gray-300 shadow-2xl">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Building2 className="h-8 w-8 text-pineapple" />
          <div>
            <p className="text-white font-bold leading-tight">Pineapple</p>
            <p className="text-xs text-gray-500">Campus Control Center</p>
          </div>
        </div>
        <div className="mt-4 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700">
          <p className="text-xs font-semibold text-pineapple uppercase tracking-wider">
            {campusName || 'Établissement'}
          </p>
        </div>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1">
        {adminNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-colors',
                isActive
                  ? 'bg-pineapple/20 text-pineapple'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500">
        Pineapple OS v3.0.0 — Admin
      </div>
    </aside>
  );
};