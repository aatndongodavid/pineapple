// frontend/src/components/layout/AdminSidebar.tsx

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Mail,
  UserCheck,
  GraduationCap,
  DoorOpen,
  ShieldCheck,
  Settings,
  CreditCard,
  FileText,
  Building2,
  Vote,
  Flag,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/lib/store/authStore';

const adminNavItems = [
  { to: '/admin', label: 'Tableau de bord', icon: LayoutDashboard, end: true },
  { to: '/admin/roster', label: 'Registre Étudiants', icon: Users },
  { to: '/admin/invitations', label: 'Invitations (Mode B)', icon: Mail },
  { to: '/admin/requests', label: 'Demandes (Mode A)', icon: UserCheck },
  { to: '/admin/classes', label: 'Gestion des Classes', icon: GraduationCap },
  { to: '/admin/rooms', label: 'Salles Physiques', icon: DoorOpen },
  { to: '/admin/delegates', label: 'Désignation Délégués', icon: ShieldCheck },
  { to: '/admin/settings', label: 'Paramètres Établissement', icon: Settings },
  { to: '/admin/subscription', label: 'Abonnement & Sièges', icon: CreditCard },
  { to: '/admin/audit', label: 'Journal d\'Audit', icon: FileText },
  { to: '/admin/democracy', label: 'Démocratie', icon: Vote },
  { to: '/admin/trust-safety', label: 'Modération', icon: Flag },
];

export const AdminSidebar: React.FC = () => {
  const { tenant } = useAuthStore();

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
        <div className="mt-4 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700 flex items-center justify-between">
          <p className="text-xs font-semibold text-pineapple uppercase tracking-wider truncate">
            {tenant?.name || 'Établissement'}
          </p>
          <span className="text-[10px] bg-pineapple/20 text-pineapple px-1.5 py-0.5 rounded font-mono font-bold">
            {tenant?.code || 'ENSPD'}
          </span>
        </div>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {adminNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-medium transition-colors',
                isActive
                  ? 'bg-pineapple/20 text-pineapple font-bold'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800 text-xs text-gray-500 flex items-center justify-between">
        <span>Pineapple OS Admin</span>
        <NavLink to="/" className="text-pineapple hover:underline">
          Quitter l'admin
        </NavLink>
      </div>
    </aside>
  );
};