// frontend/src/App.tsx

import React from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useLocation,
} from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileNav } from '@/components/layout/MobileNav';
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';
import { ProfileScreen } from '@/features/auth/ProfileScreen';
import { SecurityCenterScreen } from '@/features/auth/SecurityCenterScreen';
import { useAuthStore } from '@/lib/store/authStore';

// Layout principal pour les pages connectées
const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex bg-background-light dark:bg-background-dark">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
      <MobileNav />
    </div>
  );
};

// Composant de protection des routes
const ProtectedRoute: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();

  if (!isAuthenticated) {
    // Rediriger vers /login en conservant la destination prévue
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};

// Composant pour les routes publiques (redirige vers / si déjà connecté)
const PublicRoute: React.FC = () => {
  const { isAuthenticated } = useAuthStore();
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Routes publiques */}
        <Route element={<PublicRoute />}>
          <Route path="/login" element={<LoginScreen />} />
          <Route path="/register" element={<RegisterScreen />} />
        </Route>

        {/* Routes protégées avec layout principal */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            {/* Page d'accueil (placeholder) */}
            <Route
              path="/"
              element={
                <div className="p-6">
                  <h1 className="text-2xl font-bold">Accueil</h1>
                  <p>Bienvenue sur Pineapple OS</p>
                </div>
              }
            />
            <Route path="/profile" element={<ProfileScreen />} />
            <Route path="/security" element={<SecurityCenterScreen />} />
            {/* Ajoutez d'autres routes protégées ici au besoin */}
          </Route>
        </Route>

        {/* Redirection par défaut */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};