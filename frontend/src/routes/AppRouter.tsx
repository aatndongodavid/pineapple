// frontend/src/routes/AppRouter.tsx

import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { AdminLayout } from '@/components/layout/AdminLayout';
import { RequireAuth, RequireMembership, RequireRole } from './RouteGuards';
import { useAuthStore } from '@/lib/store/authStore';

// Public Screens
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';
import { ActivateAccountScreen } from '@/features/enrollment/ActivateAccountScreen';

// Visitor & General Screens
import { VisitorFeed } from '@/features/feed/VisitorFeed';
import { FeedScreen } from '@/features/feed/FeedScreen';
import { JoinSchoolWizard } from '@/features/enrollment/JoinSchoolWizard';
import { ProfileScreen } from '@/features/auth/ProfileScreen';
import { SecurityCenterScreen } from '@/features/auth/SecurityCenterScreen';
import { SettingsScreen } from '@/features/settings/SettingsScreen';

// Member Tool Screens
import { RoomsScreen } from '@/features/community/RoomsScreen';
import { ClassDashboardScreen } from '@/features/community/ClassDashboardScreen';
import { LibraryScreen } from '@/features/academy/LibraryScreen';
import { PineappleReaderScreen } from '@/features/academy/PineappleReaderScreen';
import { ElectionRoomScreen } from '@/democracy/ElectionRoomScreen';
import { MarketplaceScreen } from '@/features/campus_life/MarketplaceScreen';
import { PineappleRideScreen } from '@/features/campus_life/PineappleRideScreen';
import { OpportunitiesScreen } from '@/features/opportunities/OpportunitiesScreen';

// Admin Screens
import { AdminDashboardScreen } from '@/features/admin/AdminDashboardScreen';
import { AdminRosterScreen } from '@/features/admin/AdminRosterScreen';
import { AdminInvitationsScreen } from '@/features/admin/AdminInvitationsScreen';
import { AdminRequestsScreen } from '@/features/admin/AdminRequestsScreen';
import { AdminClassesScreen } from '@/features/admin/AdminClassesScreen';
import { AdminRoomsScreen } from '@/features/admin/AdminRoomsScreen';
import { AdminDelegatesScreen } from '@/features/admin/AdminDelegatesScreen';
import { AdminSettingsScreen } from '@/features/admin/AdminSettingsScreen';
import { AdminSubscriptionScreen } from '@/features/admin/AdminSubscriptionScreen';
import { AdminAuditScreen } from '@/features/admin/AdminAuditScreen';
import { IdentityVerificationScreen } from '@/features/admin/IdentityVerificationScreen';
import { DemocracyControlScreen } from '@/features/admin/DemocracyControlScreen';
import { TrustSafetyScreen } from '@/features/admin/TrustSafetyScreen';
import { MonetizationScreen } from '@/features/admin/MonetizationScreen';

// Platform Super Admin Screens
import { PlatformTenantsScreen } from '@/features/platform/PlatformTenantsScreen';

// Smart feed router (Visitor vs Member)
const SmartFeedRouter: React.FC = () => {
  const { membership } = useAuthStore();
  return membership ? <FeedScreen /> : <VisitorFeed />;
};

// 404 Screen
const NotFoundScreen: React.FC = () => {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-900 p-4">
      <div className="text-center space-y-4">
        <h1 className="text-6xl font-black text-pineapple">404</h1>
        <p className="text-gray-600 dark:text-gray-300 font-medium">Page introuvable</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-pineapple text-white text-sm font-bold rounded-xl shadow-md"
        >
          Retour au fil d'actualité
        </button>
      </div>
    </div>
  );
};

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<LoginScreen />} />
      <Route path="/register" element={<RegisterScreen />} />
      <Route path="/activate" element={<ActivateAccountScreen />} />

      {/* Main Layout Authenticated Routes */}
      <Route element={<RequireAuth />}>
        <Route element={<MainLayout />}>
          <Route path="/" element={<SmartFeedRouter />} />
          <Route path="/join-school" element={<JoinSchoolWizard />} />
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/security" element={<SecurityCenterScreen />} />
          <Route path="/settings" element={<SettingsScreen />} />

          {/* Member-Only Tools */}
          <Route element={<RequireMembership />}>
            <Route path="/rooms" element={<RoomsScreen />} />
            <Route path="/class" element={<ClassDashboardScreen />} />
            <Route path="/academy/library" element={<LibraryScreen />} />
            <Route
              path="/academy/reader/:id"
              element={<PineappleReaderScreen documentId=":id" onClose={() => window.history.back()} />}
            />
            <Route path="/democracy" element={<ElectionRoomScreen />} />
            <Route path="/democracy/:id" element={<ElectionRoomScreen />} />
            <Route path="/campus-life/marketplace" element={<MarketplaceScreen />} />
            <Route path="/campus-life/ride" element={<PineappleRideScreen />} />
            <Route path="/opportunities" element={<OpportunitiesScreen />} />
          </Route>
        </Route>
      </Route>

      {/* School Admin Routes */}
      <Route element={<RequireRole roles={['TENANT_ADMIN', 'STAFF']} />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboardScreen />} />
          <Route path="/admin/roster" element={<AdminRosterScreen />} />
          <Route path="/admin/invitations" element={<AdminInvitationsScreen />} />
          <Route path="/admin/requests" element={<AdminRequestsScreen />} />
          <Route path="/admin/classes" element={<AdminClassesScreen />} />
          <Route path="/admin/rooms" element={<AdminRoomsScreen />} />
          <Route path="/admin/delegates" element={<AdminDelegatesScreen />} />
          <Route path="/admin/settings" element={<AdminSettingsScreen />} />
          <Route path="/admin/subscription" element={<AdminSubscriptionScreen />} />
          <Route path="/admin/audit" element={<AdminAuditScreen />} />
          <Route path="/admin/identity" element={<IdentityVerificationScreen />} />
          <Route path="/admin/democracy" element={<DemocracyControlScreen />} />
          <Route path="/admin/trust-safety" element={<TrustSafetyScreen />} />
          <Route path="/admin/monetization" element={<MonetizationScreen />} />
        </Route>
      </Route>

      {/* Platform Super Admin Routes */}
      <Route element={<RequireRole roles={['PLATFORM_SUPER_ADMIN']} />}>
        <Route element={<AdminLayout />}>
          <Route path="/platform/tenants" element={<PlatformTenantsScreen />} />
        </Route>
      </Route>

      {/* Fallback 404 */}
      <Route path="*" element={<NotFoundScreen />} />
    </Routes>
  );
};
