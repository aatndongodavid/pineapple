// frontend/src/routes/AdminRoute.tsx

import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

export const AdminRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hasRole = useAuthStore((state) => state.hasRole);
  const hasHydrated = useAuthStore.persist.hasHydrated();
  const location = useLocation();

  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark">
        <Loader2 className="h-8 w-8 animate-spin text-pineapple" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const isAuthorized = hasRole('TENANT_ADMIN') || hasRole('STAFF') || hasRole('PLATFORM_SUPER_ADMIN');
  if (!isAuthorized) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
};