// frontend/src/components/layout/MobileNav.tsx

import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, DoorOpen, Megaphone, PlusCircle, User } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store/authStore';

export const MobileNav: React.FC = () => {
  const location = useLocation();
  const { membership } = useAuthStore();
  const isVisitor = !membership;

  const items = isVisitor
    ? [
        { to: '/', label: 'Fil Pubs', icon: Home },
        { to: '/join-school', label: 'Rejoindre', icon: PlusCircle },
        { to: '/profile', label: 'Profil', icon: User },
      ]
    : [
        { to: '/', label: 'Fil', icon: Home },
        { to: '/rooms', label: 'Salles', icon: DoorOpen },
        { to: '/class', label: 'Ma Classe', icon: Megaphone },
        { to: '/profile', label: 'Profil', icon: User },
      ];

  return (
    <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/90 dark:bg-slate-900/90 backdrop-blur-lg border-t border-white/20 dark:border-slate-800 shadow-xl">
      <div className={`grid grid-cols-${items.length} h-16`}>
        {items.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={cn(
              'flex flex-col items-center justify-center gap-1 text-[11px] font-medium transition-colors',
              location.pathname === item.to
                ? 'text-pineapple font-bold'
                : 'text-gray-500 dark:text-gray-400'
            )}
          >
            <item.icon className="h-5 w-5" />
            {item.label}
          </Link>
        ))}
      </div>
    </nav>
  );
};