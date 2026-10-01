// frontend/src/routes/AppRouter.tsx

import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { AdminRoute } from './AdminRoute';

// Écrans publics (chargés immédiatement)
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';
const LegalScreen = lazy(() => import('@/features/legal/LegalScreen').then(m => ({ default: m.LegalScreen })));

// Écrans protégés et administration en Code Splitting (React.lazy)
const FeedScreen = lazy(() => import('@/features/feed/FeedScreen').then(m => ({ default: m.FeedScreen })));
const ProfileScreen = lazy(() => import('@/features/auth/ProfileScreen').then(m => ({ default: m.ProfileScreen })));
const SecurityCenterScreen = lazy(() => import('@/features/auth/SecurityCenterScreen').then(m => ({ default: m.SecurityCenterScreen })));
const SettingsScreen = lazy(() => import('@/features/settings/SettingsScreen').then(m => ({ default: m.SettingsScreen })));
const OrganizationsScreen = lazy(() => import('@/features/community/OrganizationsScreen').then(m => ({ default: m.OrganizationsScreen })));
const RoomsScreen = lazy(() => import('@/features/community/RoomsScreen').then(m => ({ default: m.RoomsScreen })));
const ElectionRoomScreen = lazy(() => import('@/democracy/ElectionRoomScreen').then(m => ({ default: m.ElectionRoomScreen })));
const LibraryScreen = lazy(() => import('@/features/academy/LibraryScreen').then(m => ({ default: m.LibraryScreen })));
const PineappleReaderScreen = lazy(() => import('@/features/academy/PineappleReaderScreen').then(m => ({ default: m.PineappleReaderScreen })));
const MarketplaceScreen = lazy(() => import('@/features/campus_life/MarketplaceScreen').then(m => ({ default: m.MarketplaceScreen })));
const PineappleRideScreen = lazy(() => import('@/features/campus_life/PineappleRideScreen').then(m => ({ default: m.PineappleRideScreen })));
const OpportunitiesScreen = lazy(() => import('@/features/opportunities/OpportunitiesScreen').then(m => ({ default: m.OpportunitiesScreen })));
const ElectionCard = lazy(() => import('@/democracy/ElectionCard').then(m => ({ default: m.ElectionCard })));

// Écrans admin (lazy)
const AdminDashboardScreen = lazy(() => import('@/features/admin/AdminDashboardScreen').then(m => ({ default: m.AdminDashboardScreen })));
const IdentityVerificationScreen = lazy(() => import('@/features/admin/IdentityVerificationScreen').then(m => ({ default: m.IdentityVerificationScreen })));
const DemocracyControlScreen = lazy(() => import('@/features/admin/DemocracyControlScreen').then(m => ({ default: m.DemocracyControlScreen })));
const TrustSafetyScreen = lazy(() => import('@/features/admin/TrustSafetyScreen').then(m => ({ default: m.TrustSafetyScreen })));
const MonetizationScreen = lazy(() => import('@/features/admin/MonetizationScreen').then(m => ({ default: m.MonetizationScreen })));
const SuperAdminDashboardScreen = lazy(() => import('@/features/admin/SuperAdminDashboardScreen').then(m => ({ default: m.SuperAdminDashboardScreen })));

// ---------------------------------------------------------------
// Petit écran temporaire pour la liste des élections (ou import réel)
// ---------------------------------------------------------------
const ElectionsListScreen: React.FC = () => {
  // Exemple de données (à remplacer par un vrai store)
  const elections = [
    {
      id: 'e1',
      title: 'Élection BDE ENSPD 2027',
      electionType: 'BDE',
      status: 'VOTING_OPEN' as const,
      votingStartAt: '2027-03-15T08:00:00Z',
      votingEndAt: '2027-03-15T18:00:00Z',
    },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Élections</h1>
      {elections.map((election) => (
        <ElectionCard
          key={election.id}
          election={election}
          onClick={() => window.location.href = `/democracy/${election.id}`}
        />
      ))}
    </div>
  );
};

// ---------------------------------------------------------------
// Écran 404 (NotFound)
// ---------------------------------------------------------------
const NotFoundScreen: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 dark:text-white">404</h1>
        <p className="text-gray-500">Page introuvable</p>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------
// Routeur principal
// ---------------------------------------------------------------
export const AppRouter: React.FC = () => {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-slate-950 text-emerald-400">
          <div className="flex flex-col items-center gap-3">
            <div className="w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="text-sm font-medium tracking-wide">Chargement de Pineapple...</span>
          </div>
        </div>
      }
    >
      <Routes>
        {/* Routes publiques */}
        <Route path="/login" element={<LoginScreen />} />
        <Route path="/register" element={<RegisterScreen />} />
        <Route path="/legal" element={<LegalScreen />} />
        <Route path="/legal/:docType" element={<LegalScreen />} />

        {/* Routes protégées avec layout principal */}
        <Route element={<ProtectedRoute />}>
          <Route element={<MainLayout />}>
            <Route path="/" element={<FeedScreen />} />
            <Route path="/profile" element={<ProfileScreen />} />
            <Route path="/security" element={<SecurityCenterScreen />} />
            <Route path="/settings" element={<SettingsScreen />} />

            {/* Community : redirection d'index vers le premier onglet réel */}
            <Route path="/community" element={<Navigate to="/community/organizations" replace />} />
            <Route path="/community/organizations" element={<OrganizationsScreen />} />
            <Route path="/community/rooms" element={<RoomsScreen />} />

            <Route path="/democracy" element={<ElectionsListScreen />} />
            <Route path="/democracy/:id" element={<ElectionRoomScreen />} />

            {/* Academy : redirection d'index vers la bibliothèque */}
            <Route path="/academy" element={<Navigate to="/academy/library" replace />} />
            <Route path="/academy/library" element={<LibraryScreen />} />
            <Route
              path="/academy/reader/:id"
              element={<PineappleReaderScreen documentId=":id" onClose={() => window.history.back()} />}
            />

            {/* Campus Life : redirection d'index vers le marketplace */}
            <Route path="/campus-life" element={<Navigate to="/campus-life/marketplace" replace />} />
            <Route path="/campus-life/marketplace" element={<MarketplaceScreen />} />
            <Route path="/campus-life/ride" element={<PineappleRideScreen />} />

            <Route path="/opportunities" element={<OpportunitiesScreen />} />
          </Route>
        </Route>

        {/* Routes d'administration */}
        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin" element={<AdminDashboardScreen />} />
            <Route path="/admin/identity" element={<IdentityVerificationScreen />} />
            <Route path="/admin/democracy" element={<DemocracyControlScreen />} />
            <Route path="/admin/trust-safety" element={<TrustSafetyScreen />} />
            <Route path="/admin/monetization" element={<MonetizationScreen />} />
          </Route>
        </Route>

        {/* Route Super Admin Transverse (Gemula) */}
        <Route path="/super-admin" element={<SuperAdminDashboardScreen />} />

        {/* Fallback 404 */}
        <Route path="*" element={<NotFoundScreen />} />
      </Routes>
    </Suspense>
  );
};
