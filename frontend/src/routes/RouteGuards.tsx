// frontend/src/routes/RouteGuards.tsx

import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2, ShieldAlert, Building2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

export const RequireAuth: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const hasHydrated = useAuthStore.persist.hasHydrated();
  const location = useLocation();

  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

export const RequireMembership: React.FC = () => {
  const { membership } = useAuthStore();

  if (!membership || membership.role === 'VISITOR' || membership.status !== 'ACTIVE') {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg text-center space-y-4 border border-gray-200 dark:border-gray-700">
          <Building2 className="w-16 h-16 mx-auto text-amber-500" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Établissement requis
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Cet outil est réservé aux membres actifs d'un établissement partenaire Pineapple.
          </p>
          <a
            href="/join-school"
            className="inline-block px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-semibold rounded-lg shadow-md transition"
          >
            Rejoindre mon établissement
          </a>
        </div>
      </div>
    );
  }

  return <Outlet />;
};

export const RequirePermission: React.FC<{ permission: string }> = ({ permission }) => {
  const { can } = useAuthStore();

  if (!can(permission)) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-gray-50 dark:bg-gray-900">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl p-8 shadow-lg text-center space-y-4 border border-red-200 dark:border-red-900/30">
          <ShieldAlert className="w-16 h-16 mx-auto text-red-500" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Accès refusé
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Vous ne disposez pas des permissions requises ({permission}) pour accéder à cette fonctionnalité.
          </p>
        </div>
      </div>
    );
  }

  return <Outlet />;
};

export const RequireRole: React.FC<{ roles: string[] }> = ({ roles }) => {
  const { membership } = useAuthStore();

  if (!membership || !roles.includes(membership.role)) {
    return <Navigate to="/feed" replace />;
  }

  return <Outlet />;
};
