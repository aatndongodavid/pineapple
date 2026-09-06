// frontend/src/lib/store/identityStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

export type CertificationDocument = {
  id: string;
  userId: string;
  documentType: string;
  fileKey: string;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'CERTIFICATION_REQUIRED' | 'UNVERIFIED';
  rejectionReason?: string;
  submittedAt: string;
};

interface IdentityState {
  certificationDocuments: CertificationDocument[];
  isUploading: boolean;
  fetchCertificationStatus: () => Promise<void>;
  submitDocument: (file: File, docType: string) => Promise<void>;
  renewAnnualCertification: () => Promise<void>;
}

export const useIdentityStore = create<IdentityState>((set, get) => ({
  certificationDocuments: [],
  isUploading: false,

  fetchCertificationStatus: async () => {
    const { token } = useAuthStore.getState();
    const { tenantId } = useTenantStore.getState();

    if (!token || !tenantId) return;

    try {
      // Récupération des documents de certification (endpoint à implémenter côté backend)
      const response = await apiClient.get('/api/v1/identity/certification/documents', {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });
      set({ certificationDocuments: response.data });
    } catch (error) {
      // En cas d'échec, on conserve l'état existant
      console.error('Failed to fetch certification documents', error);
    }
  },

  submitDocument: async (file: File, docType: string) => {
    const { token } = useAuthStore.getState();
    const { tenantId } = useTenantStore.getState();

    if (!token || !tenantId) {
      throw new Error('Session invalide. Veuillez vous reconnecter.');
    }

    set({ isUploading: true });
    try {
      const formData = new FormData();
      formData.append('document_type', docType);
      formData.append('file', file);

      await apiClient.post(API_ENDPOINTS.identity.certificationSubmit, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
          'Content-Type': 'multipart/form-data',
        },
      });

      // Mise à jour optimiste : le statut passe en "Certification en attente"
      useAuthStore.getState().updateCampusStatus('Certification en attente');
      // Recharger la liste des documents
      await get().fetchCertificationStatus();
    } catch (error) {
      console.error('Failed to submit certification document', error);
      throw error;
    } finally {
      set({ isUploading: false });
    }
  },

  renewAnnualCertification: async () => {
    const { token } = useAuthStore.getState();
    const { tenantId } = useTenantStore.getState();

    if (!token || !tenantId) {
      throw new Error('Session invalide. Veuillez vous reconnecter.');
    }

    try {
      // Endpoint à implémenter : force le renouvellement de la certification
      await apiClient.post(
        '/api/v1/identity/certification/renew',
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      // Mise à jour du statut local (le backend devrait renvoyer le nouveau statut)
      useAuthStore.getState().updateCampusStatus('Certification en attente');
    } catch (error) {
      console.error('Failed to renew certification', error);
      throw error;
    }
  },
}));