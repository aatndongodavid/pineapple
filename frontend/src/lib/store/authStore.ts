// frontend/src/lib/store/authStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AuthUser {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  matricule?: string;
  filiere?: string;
  role?: 'USER' | 'STUDENT' | 'MODERATOR' | 'ADMIN' | string;
}

interface AuthState {
  token: string | null;
  user: AuthUser | null;
  tenantId: string | null;
  isAuthenticated: boolean;
  campusStatusDisplay: string | null;
  login: (token: string, user: AuthUser, campusStatusDisplay?: string) => void;
  logout: () => void;
  clearAuth: () => void;
  updateCampusStatus: (status: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      tenantId: null,
      isAuthenticated: false,
      campusStatusDisplay: null,

      login: (token, user, campusStatusDisplay) =>
        set({
          token,
          user,
          isAuthenticated: true,
          campusStatusDisplay: campusStatusDisplay || null,
        }),

      logout: () =>
        set({
          token: null,
          user: null,
          tenantId: null,
          isAuthenticated: false,
          campusStatusDisplay: null,
        }),

      clearAuth: () =>
        set({
          token: null,
          user: null,
          tenantId: null,
          isAuthenticated: false,
          campusStatusDisplay: null,
        }),

      updateCampusStatus: (status) =>
        set({ campusStatusDisplay: status }),
    }),
    {
      name: 'pineapple-auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        tenantId: state.tenantId,
        isAuthenticated: state.isAuthenticated,
        campusStatusDisplay: state.campusStatusDisplay,
      }),
    }
  )
);
