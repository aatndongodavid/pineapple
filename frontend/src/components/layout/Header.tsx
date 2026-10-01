// frontend/src/components/layout/Header.tsx

import React from 'react';
import { Bell, ChevronDown, UserCircle } from 'lucide-react';
import { LogoMark } from '@/components/ui/LogoMark';

const tenants = [
  { id: '1', name: 'ENSPD' },
  { id: '2', name: 'UDo' },
  { id: '3', name: 'ENS' },
];

interface HeaderProps {
  onChatClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onChatClick }) => {
  const [selectedTenant, setSelectedTenant] = React.useState(tenants[0]);
  const [notifications] = React.useState(3);

  return (
    <header className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 py-3 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md border-b border-stone-200 dark:border-stone-800 shadow-sm">
      {/* Sélecteur d'établissement & Brand logo */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 md:hidden">
          <LogoMark size={28} />
          <span className="font-bold text-lg text-primary tracking-tight">Pineapple</span>
        </div>
        <span className="hidden sm:inline text-sm text-stone-500 dark:text-stone-400">
          Établissement :
        </span>
        <div className="relative group">
          <button className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-stone-100 dark:bg-slate-800 text-stone-700 dark:text-stone-200 text-sm font-medium border border-stone-200 dark:border-stone-700">
            {selectedTenant.name}
            <ChevronDown className="h-4 w-4" />
          </button>
          <div className="absolute hidden group-hover:block top-full mt-1 w-48 bg-white dark:bg-slate-900 rounded-xl shadow-card border border-stone-200 dark:border-stone-800 p-1">
            {tenants.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelectedTenant(t)}
                className="w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-primary/10 text-stone-700 dark:text-stone-200"
              >
                {t.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Notifications + Avatar */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onChatClick}
          aria-label="Voir les notifications"
          className="relative p-2 rounded-full hover:bg-primary/10 transition-colors"
        >
          <Bell className="h-5 w-5 text-stone-600 dark:text-stone-300" />
          {notifications > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-danger text-white text-xs w-5 h-5 flex items-center justify-center rounded-full font-bold">
              {notifications}
            </span>
          )}
        </button>
        <button type="button" aria-label="Profil utilisateur" className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center">
            <UserCircle className="h-6 w-6 text-primary" />
          </div>
        </button>
      </div>
    </header>
  );
};
