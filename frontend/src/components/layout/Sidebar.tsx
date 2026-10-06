// frontend/src/components/layout/Sidebar.tsx

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  DoorOpen,
  Users,
  Vote,
  GraduationCap,
  Briefcase,
  ShoppingBag,
  User,
  ShieldAlert,
  Building2,
  Megaphone,
  PlusCircle,
  ShieldCheck,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store/authStore';

export const Sidebar: React.FC = () => {
  const { membership, can, hasRole, user } = useAuthStore();

  const isVisitor = !membership;
  const isDelegate = can('class.announce');
  const isTenantAdmin = hasRole('TENANT_ADMIN') || hasRole('STAFF');
  const isPlatformAdmin = hasRole('PLATFORM_SUPER_ADMIN');

  return (
    <aside className="hidden md:flex flex-col w-64 h-screen bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-r border-white/20 dark:border-slate-800 shadow-xl">
      {/* Logo */}
      <div className="flex items-center gap-3 p-6">
        <div className="w-10 h-10 rounded-xl bg-pineapple flex items-center justify-center text-white font-bold text-xl shadow-md">
          P
        </div>
        <div>
          <span className="text-lg font-bold text-gray-800 dark:text-white leading-none">
            Pineapple
          </span>
          <p className="text-[10px] text-gray-400 font-semibold tracking-wider uppercase">
            {isVisitor ? 'Mode Visiteur' : 'Campus Hub'}
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 space-y-1 overflow-y-auto">
        <NavLink
          to="/"
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
              'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
              isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
            )
          }
        >
          <Home className="h-5 w-5" />
          Fil d'actualité
        </NavLink>

        {isVisitor ? (
          <NavLink
            to="/join-school"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all',
                'bg-pineapple text-white hover:bg-pineapple-hover shadow-md',
                isActive ? 'ring-2 ring-pineapple/50' : ''
              )
            }
          >
            <PlusCircle className="h-5 w-5" />
            Rejoindre mon école
          </NavLink>
        ) : (
          <>
            <NavLink
              to="/rooms"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <DoorOpen className="h-5 w-5" />
              Salles
            </NavLink>

            <NavLink
              to="/class"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <Megaphone className="h-5 w-5" />
              Ma Classe
            </NavLink>

            <NavLink
              to="/academy/library"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <GraduationCap className="h-5 w-5" />
              Academy
            </NavLink>

            <NavLink
              to="/democracy"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <Vote className="h-5 w-5" />
              Démocratie
            </NavLink>

            <NavLink
              to="/campus-life/marketplace"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <ShoppingBag className="h-5 w-5" />
              Market & Covoiturage
            </NavLink>

            <NavLink
              to="/opportunities"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                  isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
                )
              }
            >
              <Briefcase className="h-5 w-5" />
              Opportunités
            </NavLink>
          </>
        )}

        <div className="pt-4 border-t border-gray-100 dark:border-slate-800 space-y-1">
          {isTenantAdmin && (
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all',
                  'bg-gray-900 text-white dark:bg-slate-800 hover:bg-black',
                  isActive ? 'ring-2 ring-pineapple' : ''
                )
              }
            >
              <Building2 className="h-5 w-5 text-pineapple" />
              Admin Établissement
            </NavLink>
          )}

          {isPlatformAdmin && (
            <NavLink
              to="/platform/tenants"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all',
                  'bg-amber-600 text-white hover:bg-amber-700',
                  isActive ? 'ring-2 ring-white' : ''
                )
              }
            >
              <ShieldCheck className="h-5 w-5" />
              Super Admin
            </NavLink>
          )}

          <NavLink
            to="/profile"
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                'text-gray-600 dark:text-gray-400 hover:bg-pineapple/10 hover:text-pineapple',
                isActive ? 'bg-pineapple/15 text-pineapple shadow-sm font-bold' : ''
              )
            }
          >
            <User className="h-5 w-5" />
            Profil & Compte
          </NavLink>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-gray-100 dark:border-slate-800 text-xs text-gray-400 flex items-center justify-between">
        <span>Pineapple OS v3.0</span>
        {membership && (
          <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 font-bold text-[10px]">
            MEMBRE
          </span>
        )}
      </div>
    </aside>
  );
};