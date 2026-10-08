import React from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
} from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { MobileNav } from '@/components/layout/MobileNav';

// Auth Screens
import { LoginScreen } from '@/features/auth/LoginScreen';
import { RegisterScreen } from '@/features/auth/RegisterScreen';
import { ProfileScreen } from '@/features/auth/ProfileScreen';
import { SecurityCenterScreen } from '@/features/auth/SecurityCenterScreen';

// Core Screens
import { DemoHomeScreen } from '@/features/demo/DemoHomeScreen';
import { RoomsScreen } from '@/features/community/RoomsScreen';
import { ClassDashboardScreen } from '@/features/community/ClassDashboardScreen';
import { VotingBoothScreen } from '@/democracy/VotingBoothScreen';

// Admin Screens
import { AdminDashboardScreen } from '@/features/admin/AdminDashboardScreen';
import { AdminRosterScreen } from '@/features/admin/AdminRosterScreen';
import { AdminRoomsScreen } from '@/features/admin/AdminRoomsScreen';
import { AdminDelegatesScreen } from '@/features/admin/AdminDelegatesScreen';
import { AdminClassesScreen } from '@/features/admin/AdminClassesScreen';
import { AdminSettingsScreen } from '@/features/admin/AdminSettingsScreen';
import { AdminSubscriptionScreen } from '@/features/admin/AdminSubscriptionScreen';
import { AdminAuditScreen } from '@/features/admin/AdminAuditScreen';

const MainLayout: React.FC = () => {
  return (
    <div className="min-h-screen flex bg-slate-950 text-slate-100 font-sans">
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

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          {/* Main Dashboard & Navigation Routes */}
          <Route path="/" element={<DemoHomeScreen />} />
          <Route path="/rooms" element={<RoomsScreen />} />
          <Route path="/class" element={<ClassDashboardScreen />} />
          <Route path="/academy/library" element={<AdminRosterScreen />} />
          <Route path="/democracy" element={<VotingBoothScreen />} />

          {/* Admin Section Routes */}
          <Route path="/admin" element={<AdminDashboardScreen />} />
          <Route path="/admin/roster" element={<AdminRosterScreen />} />
          <Route path="/admin/rooms" element={<AdminRoomsScreen />} />
          <Route path="/admin/delegates" element={<AdminDelegatesScreen />} />
          <Route path="/admin/classes" element={<AdminClassesScreen />} />
          <Route path="/admin/settings" element={<AdminSettingsScreen />} />
          <Route path="/admin/subscription" element={<AdminSubscriptionScreen />} />
          <Route path="/admin/audit" element={<AdminAuditScreen />} />

          {/* User Account & Security Routes */}
          <Route path="/profile" element={<ProfileScreen />} />
          <Route path="/security" element={<SecurityCenterScreen />} />
          <Route path="/login" element={<LoginScreen />} />
          <Route path="/register" element={<RegisterScreen />} />
        </Route>
        
        {/* Fallback to Dashboard */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};