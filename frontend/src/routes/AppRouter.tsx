// frontend/src/routes/AppRouter.tsx

import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { AdminRoute } from './AdminRoute';

// Import des écrans publics
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';

// Import des écrans protégés (utilisateurs)
import { FeedScreen } from '@/features/feed/FeedScreen';
import { ProfileScreen } from '@/features/auth/ProfileScreen';
import { SecurityCenterScreen } from '@/features/auth/SecurityCenterScreen';
import { SettingsScreen } from '@/features/settings/SettingsScreen';
import { OrganizationsScreen } from '@/features/community/OrganizationsScreen';
import { RoomsScreen } from '@/features/community/RoomsScreen';
import { ElectionRoomScreen } from '@/features/democracy/ElectionRoomScreen';
import { LibraryScreen } from '@/features/academy/LibraryScreen';
import { PineappleReaderScreen } from '@/features/academy/PineappleReaderScreen';
import { MarketplaceScreen } from '@/features/campus_life/MarketplaceScreen';
import { PineappleRideScreen } from '@/features/campus_life/PineappleRideScreen';
import { OpportunitiesScreen } from '@/features/opportunities/OpportunitiesScreen';
import { ElectionCard } from '@/features/democracy/ElectionCard';

// Import des écrans admin
import { AdminDashboardScreen } from '@/features/admin/AdminDashboardScreen';
import { IdentityVerificationScreen } from '@/features/admin/IdentityVerificationScreen';
import { DemocracyControlScreen } from '@/features/admin/DemocracyControlScreen';
import { TrustSafetyScreen } from '@/features/admin/TrustSafetyScreen';
import { MonetizationScreen } from '@/features/admin/MonetizationScreen';

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
      status: 'VOTING_OPEN',
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
    <Routes>
      {/* Routes publiques */}
      <Route path="/login" element={<LoginScreen />} />
      <Route path="/register" element={<RegisterScreen />} />

      {/* Routes protégées avec layout principal */}
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<FeedScreen />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/security" element={<SecurityCenterScreen />} />
          <Route path="/settings" element={<SettingsScreen />} />

          <Route path="/community/organizations" element={<OrganizationsScreen />} />
          <Route path="/community/rooms" element={<RoomsScreen />} />

          <Route path="/democracy" element={<ElectionsListScreen />} />
          <Route path="/democracy/:id" element={<ElectionRoomScreen />} />

          <Route path="/academy/library" element={<LibraryScreen />} />
          <Route
            path="/academy/reader/:id"
            element={<PineappleReaderScreen documentId=":id" onClose={() => window.history.back()} />}
          />

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

      {/* Fallback 404 */}
      <Route path="*" element={<NotFoundScreen />} />
    </Routes>
  );
};