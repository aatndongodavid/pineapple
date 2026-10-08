// frontend/src/lib/store/authStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: string;

  // Backwards compatibility aliases for legacy components
  role?: string;
  firstName?: string;
  lastName?: string;
  matricule?: string;
  filiere?: string;
}

export interface UserMembership {
  id: string | null;
  role: 'VISITOR' | 'STUDENT' | 'DELEGATE' | 'TEACHER' | 'STAFF' | 'TENANT_ADMIN' | 'PLATFORM_SUPER_ADMIN' | string;
  status: 'NONE' | 'PENDING' | 'ACTIVE' | 'SUSPENDED' | 'ENDED' | string;
}

export interface TenantInfo {
  id: string;
  name: string;
  code: string;
}

export interface ClassGroupInfo {
  id: string;
  name: string;
  code: string;
}

interface AuthState {
  token: string | null;
  user: UserProfile | null;
  membership: UserMembership | null;
  tenant: TenantInfo | null;
  classGroup: ClassGroupInfo | null;
  delegateOf: string[];
  permissions: string[];
  subscriptionState: string;
  campusStatusDisplay: string | null;
  isAuthenticated: boolean;

  setAuthData: (token: string, meData: any) => void;
  login: (token: string, user: any) => void;
  logout: () => void;
  clearAuth: () => void;
  updateCampusStatus: (status: string) => void;
  can: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      membership: null,
      tenant: null,
      classGroup: null,
      delegateOf: [],
      permissions: [],
      subscriptionState: 'ACTIVE',
      campusStatusDisplay: null,
      isAuthenticated: false,

      setAuthData: (token, meData) => {
        const user = meData.user ? {
          id: meData.user.id,
          email: meData.user.email,
          first_name: meData.user.first_name,
          last_name: meData.user.last_name,
          user_type: meData.user.user_type,
          role: meData.membership?.role || 'VISITOR',
          firstName: meData.user.first_name,
          lastName: meData.user.last_name,
        } : null;

        const membership = meData.membership ? {
          id: meData.membership.id,
          role: meData.membership.role || 'VISITOR',
          status: meData.membership.status || 'NONE',
        } : { id: null, role: 'VISITOR', status: 'NONE' };

        set({
          token,
          user,
          membership,
          tenant: meData.tenant || null,
          classGroup: meData.class_group || null,
          delegateOf: meData.delegate_of || [],
          permissions: meData.permissions || [],
          subscriptionState: meData.subscription_state || 'ACTIVE',
          campusStatusDisplay: meData.campus_status_display || 'Visiteur',
          isAuthenticated: true,
        });
      },

      login: (token, user) => {
        set({
          token,
          user: {
            ...user,
            first_name: user.first_name || user.firstName || '',
            last_name: user.last_name || user.lastName || '',
            firstName: user.firstName || user.first_name || '',
            lastName: user.lastName || user.last_name || '',
            role: user.role || 'VISITOR',
          },
          isAuthenticated: true,
        });
      },

      logout: () =>
        set({
          token: null,
          user: null,
          membership: null,
          tenant: null,
          classGroup: null,
          delegateOf: [],
          permissions: [],
          subscriptionState: 'ACTIVE',
          campusStatusDisplay: null,
          isAuthenticated: false,
        }),

      clearAuth: () =>
        set({
          token: null,
          user: null,
          membership: null,
          tenant: null,
          classGroup: null,
          delegateOf: [],
          permissions: [],
          subscriptionState: 'ACTIVE',
          campusStatusDisplay: null,
          isAuthenticated: false,
        }),

      updateCampusStatus: (status: string) => set({ campusStatusDisplay: status }),

      can: (permission: string) => {
        const state = get();
        if (!state.isAuthenticated) return false;
        if (state.membership?.role === 'PLATFORM_SUPER_ADMIN') return true;
        return state.permissions.includes(permission);
      },

      hasRole: (role: string) => {
        const state = get();
        if (!state.isAuthenticated) return false;
        return state.membership?.role === role || state.user?.role === role;
      },
    }),
    {
      name: 'pineapple-auth-storage',
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        membership: state.membership,
        tenant: state.tenant,
        classGroup: state.classGroup,
        delegateOf: state.delegateOf,
        permissions: state.permissions,
        subscriptionState: state.subscriptionState,
        campusStatusDisplay: state.campusStatusDisplay,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
