import React from 'react';
import { Bell, ChevronDown, ShieldAlert } from 'lucide-react';

const tenants = [
  { id: '00000000-0000-0000-0000-000000000000', name: 'Établissement Démo Pineapple' },
  { id: '1', name: 'Université de Douala - FSEGA' },
  { id: '2', name: 'ENSPD - Polytechnique Douala' },
];

interface HeaderProps {
  onChatClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onChatClick }) => {
  const [selectedTenant, setSelectedTenant] = React.useState(tenants[0]);

  return (
    <div className="flex flex-col">
      {/* Persistent Demo Banner (Gate W5) */}
      <div className="bg-gradient-to-r from-amber-500 via-amber-600 to-amber-500 text-slate-950 font-extrabold text-xs py-2 px-4 flex items-center justify-center gap-2 shadow-md z-50">
        <ShieldAlert className="h-4 w-4 text-slate-950 animate-bounce" />
        <span>⚠️ MODE DÉMONSTRATION — BAC À SABLE PINEAPPLE (Réinitialisation automatique chaque nuit)</span>
      </div>

      {/* Main Header Bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-4 md:px-6 py-3.5 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 text-white shadow-md">
        {/* Tenant Selector */}
        <div className="flex items-center gap-3">
          <span className="hidden sm:inline text-xs font-semibold text-slate-400">
            Établissement Actif :
          </span>
          <div className="relative group">
            <button className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-800 border border-slate-700 text-white text-xs font-bold hover:bg-slate-700 transition-colors">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              {selectedTenant.name}
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>
            <div className="absolute hidden group-hover:block top-full left-0 mt-1 w-64 bg-slate-900 rounded-xl shadow-2xl border border-slate-800 p-1 z-50">
              {tenants.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setSelectedTenant(t)}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs font-medium text-slate-300 hover:bg-amber-500/10 hover:text-amber-400 transition-colors"
                >
                  {t.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right User & Status Profile */}
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={onChatClick}
            className="relative p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors border border-slate-700"
            title="Notifications"
          >
            <Bell className="h-4 w-4 text-slate-300" />
            <span className="absolute -top-1 -right-1 bg-amber-500 text-slate-950 font-bold text-[10px] w-4 h-4 flex items-center justify-center rounded-full">
              3
            </span>
          </button>

          <div className="flex items-center gap-2 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
            <div className="w-7 h-7 rounded-lg bg-amber-500 flex items-center justify-center font-bold text-slate-950 text-xs">
              🍍
            </div>
            <div className="hidden sm:block text-left">
              <span className="block text-xs font-bold text-white">Admin Démo</span>
              <span className="block text-[10px] text-amber-400 font-semibold">TENANT_ADMIN</span>
            </div>
          </div>
        </div>
      </header>
    </div>
  );
};
