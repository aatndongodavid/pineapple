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
import { LogoMark } from '@/components/ui/LogoMark';

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
    <aside className="hidden md:flex flex-col w-64 h-screen bg-white/90 dark:bg-stone-900/90 backdrop-blur-md border-r border-stone-200 dark:border-stone-800 shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6 border-b border-stone-100 dark:border-stone-800">
        <LogoMark size={36} />
        <span className="text-xl font-bold tracking-tight text-stone-900 dark:text-white">
          Pineapple
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                'text-stone-600 dark:text-stone-400 hover:bg-primary-light/10 hover:text-primary',
                isActive
                  ? 'bg-primary/10 text-primary font-semibold border-r-2 border-primary'
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
      <div className="p-4 text-xs text-stone-400 dark:text-stone-500 border-t border-stone-100 dark:border-stone-800">
        Pineapple OS v3.0.0
      </div>
    </aside>
  );
};