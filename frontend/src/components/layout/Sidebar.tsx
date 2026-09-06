// frontend/src/components/layout/Sidebar.tsx

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Users,
  Vote,
  GraduationCap,
  Briefcase,
  ShoppingBag,
  User,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navItems = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/community', label: 'Community', icon: Users },
  { to: '/democracy', label: 'Democracy', icon: Vote },
  { to: '/academy', label: 'Academy', icon: GraduationCap },
  { to: '/opportunities', label: 'Opportunities', icon: Briefcase },
  { to: '/campus-life', label: 'Campus Life', icon: ShoppingBag },
  { to: '/profile', label: 'Profil', icon: User },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="hidden md:flex flex-col w-64 h-screen bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-r border-white/20 dark:border-slate-800 shadow-xl">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6">
        <div className="w-10 h-10 rounded-xl bg-pineapple flex items-center justify-center text-white font-bold text-xl">
          P
        </div>
        <span className="text-lg font-semibold text-gray-800 dark:text-white">
          Pineapple
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                isActive
                  ? 'bg-pineapple/15 text-pineapple shadow-neo-inset dark:shadow-neo-dark-inset'
                  : ''
              )
            }
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Version */}
      <div className="p-4 text-xs text-gray-400">Pineapple OS v3.0.0</div>
    </aside>
  );
};