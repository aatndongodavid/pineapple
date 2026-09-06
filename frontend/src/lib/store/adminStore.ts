// frontend/src/lib/store/adminStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface CertificationRequest {
  id: string;
  first_name: string;
  last_name: string;
  matricule: string;
  filiere: string;
  submitted_at: string;
  document_url?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
}

export interface Report {
  id: string;
  target_type: string;
  reason: string;
  reporter_name: string;
  status: 'PENDING' | 'INVESTIGATING' | 'RESOLVED' | 'DISMISSED';
  content: string;
  target_name: string;
}

export interface CampusLicenseStats {
  tier: 'BASIC' | 'STANDARD' | 'ENTERPRISE';
  max_certified_students: number;
  current_certified_students: number;
  expires_at: string;
}

interface AdminState {
  pendingCertifications: CertificationRequest[];
  activeReports: Report[];
  campusLicenseStats: CampusLicenseStats | null;
  isLoading: boolean;
  error: string | null;

  fetchPendingCertifications: () => Promise<void>;
  approveCertification: (userId: string) => Promise<void>;
  rejectCertification: (userId: string, reason: string) => Promise<void>;
  fetchReports: () => Promise<void>;
  resolveReport: (reportId: string, action: string) => Promise<void>;
  fetchCampusLicense: () => Promise<void>;
}

export const useAdminStore = create<AdminState>((set) => ({
  pendingCertifications: [],
  activeReports: [],
  campusLicenseStats: null,
  isLoading: false,
  error: null,

  fetchPendingCertifications: async () => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get(
        '/api/v1/admin/identity/certifications/pending',
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      set({ pendingCertifications: response.data, isLoading: false });
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants', isLoading: false });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur de chargement', isLoading: false });
      }
    }
  },

  approveCertification: async (userId: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      await apiClient.post(
        '/api/v1/admin/identity/certifications/approve',
        { user_id: userId },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      // Retirer l'élément de la liste locale
      set((state) => ({
        pendingCertifications: state.pendingCertifications.filter(
          (c) => c.id !== userId
        ),
      }));
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants' });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur lors de l’approbation' });
      }
    }
  },

  rejectCertification: async (userId: string, reason: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      await apiClient.post(
        '/api/v1/admin/identity/certifications/reject',
        { user_id: userId, reason },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      set((state) => ({
        pendingCertifications: state.pendingCertifications.filter(
          (c) => c.id !== userId
        ),
      }));
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants' });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur lors du rejet' });
      }
    }
  },

  fetchReports: async () => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get('/api/v1/admin/trust-safety/reports', {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });
      set({ activeReports: response.data, isLoading: false });
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants', isLoading: false });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur de chargement', isLoading: false });
      }
    }
  },

  resolveReport: async (reportId: string, action: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      await apiClient.post(
        '/api/v1/admin/trust-safety/reports/resolve',
        { report_id: reportId, action },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      set((state) => ({
        activeReports: state.activeReports.filter((r) => r.id !== reportId),
      }));
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants' });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur lors de la résolution' });
      }
    }
  },

  fetchCampusLicense: async () => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get(API_ENDPOINTS.monetization.licenseStatus, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });
      set({ campusLicenseStats: response.data, isLoading: false });
    } catch (err: any) {
      if (err.response?.status === 403) {
        set({ error: 'Droits administrateur insuffisants', isLoading: false });
      } else {
        set({ error: err.response?.data?.detail || 'Erreur de chargement', isLoading: false });
      }
    }
  },
}));