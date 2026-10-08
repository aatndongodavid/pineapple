import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  DoorOpen,
  Vote,
  GraduationCap,
  User,
  Building2,
  Megaphone,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store/authStore';

export const Sidebar: React.FC = () => {
  const { membership, hasRole } = useAuthStore();

  const isTenantAdmin = hasRole('TENANT_ADMIN') || hasRole('STAFF') || true;

  return (
    <aside className="hidden md:flex flex-col w-64 h-screen bg-slate-950 border-r border-slate-800 text-slate-300 shadow-2xl">
      {/* Logo & Brand Header matching website */}
      <a href="/" className="flex items-center gap-3 p-6 group border-b border-slate-800/80">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center font-bold text-slate-950 text-xl shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform">
          🍍
        </div>
        <div>
          <span className="font-extrabold text-lg tracking-tight text-white group-hover:text-amber-400 transition-colors">
            Pineapple OS
          </span>
          <span className="block text-[10px] text-amber-400 font-semibold tracking-wider uppercase">
            Bac à sable Démo
          </span>
        </div>
      </a>

      {/* Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        <NavLink
          to="/"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-bold transition-all',
              'text-slate-300 hover:bg-slate-800 hover:text-amber-400',
              isActive ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md font-extrabold' : ''
            )
          }
        >
          <Home className="h-4 w-4" />
          Tableau de Bord
        </NavLink>

        <NavLink
          to="/rooms"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all',
              'text-slate-300 hover:bg-slate-800 hover:text-amber-400',
              isActive ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md font-extrabold' : ''
            )
          }
        >
          <DoorOpen className="h-4 w-4" />
          Salles & Amphis
        </NavLink>

        <NavLink
          to="/class"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all',
              'text-slate-300 hover:bg-slate-800 hover:text-amber-400',
              isActive ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md font-extrabold' : ''
            )
          }
        >
          <Megaphone className="h-4 w-4" />
          Espace Délégués
        </NavLink>

        <NavLink
          to="/academy/library"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all',
              'text-slate-300 hover:bg-slate-800 hover:text-amber-400',
              isActive ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md font-extrabold' : ''
            )
          }
        >
          <GraduationCap className="h-4 w-4" />
          Scolarité & Registres
        </NavLink>

        <NavLink
          to="/democracy"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-semibold transition-all',
              'text-slate-300 hover:bg-slate-800 hover:text-amber-400',
              isActive ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 shadow-md font-extrabold' : ''
            )
          }
        >
          <Vote className="h-4 w-4" />
          Élections Délégués
        </NavLink>

        <div className="pt-4 border-t border-slate-800/80 space-y-1.5">
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-extrabold transition-all',
                'bg-slate-900 text-amber-400 hover:bg-slate-800 border border-slate-800',
                isActive ? 'ring-2 ring-amber-500' : ''
              )
            }
          >
            <Building2 className="h-4 w-4 text-amber-400" />
            Administration Scolarité
          </NavLink>

          <NavLink
            to="/profile"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-medium transition-all',
                'text-slate-400 hover:bg-slate-800 hover:text-white',
                isActive ? 'bg-slate-800 text-white font-bold' : ''
              )
            }
          >
            <User className="h-4 w-4" />
            Mon Profil Démo
          </NavLink>
        </div>
      </nav>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Pineapple OS v3.0</span>
        <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-extrabold text-[10px]">
          DÉMO ACTIVES
        </span>
      </div>
    </aside>
  );
};