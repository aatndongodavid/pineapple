// frontend/src/routes/AdminRoute.tsx

import React from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuthStore } from '@/lib/store/authStore';

/**
 * Route d'administration : exige que l'utilisateur soit authentifié
 * ET qu'il possède le rôle ADMIN ou MODERATOR.
 * Redirige vers / (ou une page 403) si les droits sont insuffisants.
 */
export const AdminRoute: React.FC = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  const user = useAuthStore((state) => state.user);
  const hasHydrated = useAuthStore.persist.hasHydrated();
  const location = useLocation();

  // Pendant l'hydratation, spinner
  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background-light dark:bg-background-dark">
        <Loader2 className="h-8 w-8 animate-spin text-pineapple" />
      </div>
    );
  }

  // Vérification de l'authentification
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Vérification du rôle administrateur / modérateur
  const role = user?.role; // champ role supposé sur l'utilisateur
  if (role !== 'ADMIN' && role !== 'MODERATOR') {
    // Rediriger vers l'accueil (ou /403 si on souhaite une page dédiée)
    return <Navigate to="/" replace />;
  }

  // L'utilisateur est authentifié et a les droits : on rend les enfants
  return <Outlet />;
};