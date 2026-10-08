// frontend/src/components/layout/AdminLayout.tsx

import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';
import { useAuthStore } from '@/lib/store/authStore';

export const AdminLayout: React.FC = () => {
  const { hasRole } = useAuthStore();
  const isAuthorized = hasRole('TENANT_ADMIN') || hasRole('STAFF') || hasRole('PLATFORM_SUPER_ADMIN');

  if (!isAuthorized) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen flex bg-gray-100 dark:bg-slate-950">
      <AdminSidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 flex items-center justify-between px-6 py-3 bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800">
          <h1 className="text-lg font-semibold text-gray-800 dark:text-white">
            Administration Établissement
          </h1>
          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-300">
            <span className="px-2.5 py-0.5 rounded-full bg-pineapple/10 text-pineapple font-bold text-xs">
              Mode Admin
            </span>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};