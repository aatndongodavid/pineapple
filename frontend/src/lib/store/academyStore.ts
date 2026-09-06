// frontend/src/lib/store/academyStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// Types simplifiés (alignés sur les DTOs backend)
export type DocumentType = 'COURSE' | 'TD' | 'TP' | 'EXAM' | 'CORRIGE_PREMIUM' | 'RESEARCH_PAPER';

export interface LibraryDocument {
  id: string;
  tenant_id: string;
  title: string;
  document_type: DocumentType;
  faculty: string;
  filiere: string;
  academic_level: string;
  is_premium: boolean;
  price_fcfa: number;
  // Champ additionnel pour l'affichage
  access_status?: 'FREE' | 'PREMIUM_LOCKED' | 'PURCHASED' | 'UNLIMITED';
}

interface AcademyState {
  documents: LibraryDocument[];
  purchasedDocuments: LibraryDocument[];
  isLoading: boolean;
  error: string | null;
  fetchLibrary: (tenantId: string, filters?: { faculty?: string; level?: string; docType?: string }) => Promise<void>;
  purchaseDocument: (documentId: string) => Promise<void>;
  loadReaderStream: (documentId: string) => Promise<Blob | null>;
}

export const useAcademyStore = create<AcademyState>((set) => ({
  documents: [],
  purchasedDocuments: [],
  isLoading: false,
  error: null,

  fetchLibrary: async (tenantId, filters = {}) => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      if (!token) throw new Error('Non authentifié');

      const params = new URLSearchParams();
      if (filters.faculty) params.append('faculty', filters.faculty);
      if (filters.level) params.append('level', filters.level);
      if (filters.docType) params.append('doc_type', filters.docType);

      const response = await apiClient.get(API_ENDPOINTS.academy.library, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        params,
      });

      set({ documents: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement de la bibliothèque',
        isLoading: false,
      });
    }
  },

  purchaseDocument: async (documentId) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      await apiClient.post(
        API_ENDPOINTS.academy.purchase,
        { document_id: documentId, payment_method: 'mobile_money' },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      // Optionnel : refetch des documents achetés
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Erreur lors de l\'achat' });
    }
  },

  loadReaderStream: async (documentId) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get(API_ENDPOINTS.academy.readerStream(documentId), {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        responseType: 'blob',
      });

      return response.data as Blob;
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Erreur lors du chargement du document' });
      return null;
    }
  },
}));