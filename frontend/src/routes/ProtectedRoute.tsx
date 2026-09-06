// frontend/src/routes/ProtectedRoute.tsx

import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

/**
 * Route protégée : exige que l'utilisateur soit authentifié.
 * Redirige vers /login avec l'URL cible en state pour y revenir après connexion.
 * Affiche un spinner tant que l'hydratation du store n'est pas terminée.
 */
export const ProtectedRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const hasHydrated = useAuthStore.persist.hasHydrated();
  const location = useLocation();

  // Pendant l'hydratation, on affiche un spinner
  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark">
        <Loader2 className="h-8 w-8 animate-spin text-pineapple" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirection vers /login en conservant la destination
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // L'utilisateur est authentifié : on rend les enfants via Outlet
  return <Outlet />;
};