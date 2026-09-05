// frontend/src/components/layout/Header.tsx

import React from 'react';
import { Bell, ChevronDown, UserCircle } from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

// Simulons un sélecteur de tenant avec un simple dropdown
const tenants = [
  { id: '1', name: 'ENSPD' },
  { id: '2', name: 'UDo' },
  { id: '3', name: 'ENS' },
];

export const Header: React.FC = () => {
  const [selectedTenant, setSelectedTenant] = React.useState(tenants[0]);
  const [notifications] = React.useState(3); // à remplacer par un store

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 py-3 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-white/20 dark:border-slate-800 shadow-sm">
      {/* Sélecteur d'établissement */}
      <div className="flex items-center gap-2">
        <span className="hidden sm:inline text-sm text-gray-500 dark:text-gray-400">
          Établissement :
        </span>
        <div className="relative group">
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-background-light dark:bg-slate-800 text-gray-700 dark:text-gray-200 text-sm font-medium">
            {selectedTenant.name}
            <ChevronDown className="h-4 w-4" />
          </button>
          <div className="absolute hidden group-hover:block top-full mt-1 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-neo-extruded dark:shadow-neo-dark-extruded border border-white/20 dark:border-slate-800 p-1">
            {tenants.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedTenant(t)}
                className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-pineapple/10"
              >
                {t.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Notifications + Avatar */}
      <div className="flex items-center gap-4">
        <button className="relative p-2 rounded-full hover:bg-pineapple/10 transition-colors">
          <Bell className="h-5 w-5 text-gray-600 dark:text-gray-300" />
          {notifications > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs w-5 h-5 flex items-center justify-center rounded-full">
              {notifications}
            </span>
          )}
        </button>
        <button className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-pineapple/20 flex items-center justify-center">
            <UserCircle className="h-6 w-6 text-pineapple" />
          </div>
        </button>
      </div>
    </header>
  );
};