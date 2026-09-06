// frontend/src/lib/store/opportunitiesStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types (alignés sur les DTOs backend)
// ---------------------------------------------------------------------------
export type OpportunityType = 'PROJECT' | 'RESEARCH' | 'CHALLENGE' | 'INTERNSHIP' | 'STARTUP';
export type OpportunityStatus = 'DRAFT' | 'OPEN' | 'CLOSED' | 'ARCHIVED';
export type ApplicationStatus = 'PENDING' | 'ACCEPTED' | 'REJECTED';

export interface Opportunity {
  id: string;
  tenant_id: string;
  creator_id: string;
  title: string;
  description: string;
  type: OpportunityType;
  required_skills: string[];
  status: OpportunityStatus;
  max_applicants?: number | null;
  created_at: string;
}

export interface OpportunityApplication {
  id: string;
  opportunity_id: string;
  applicant_user_id: string;
  cover_letter: string;
  status: ApplicationStatus;
  applied_at: string;
}

export interface OpportunityCreateDTO {
  title: string;
  description: string;
  type: OpportunityType;
  required_skills: string[];
  max_applicants?: number | null;
  status: OpportunityStatus;
}

// ---------------------------------------------------------------------------
// Store Zustand
// ---------------------------------------------------------------------------
interface OpportunitiesState {
  opportunities: Opportunity[];
  userApplications: OpportunityApplication[];
  isLoading: boolean;
  error: string | null;

  fetchOpportunities: (type?: OpportunityType | 'ALL') => Promise<void>;
  applyToOpportunity: (opportunityId: string, coverLetter: string) => Promise<void>;
  createOpportunity: (data: OpportunityCreateDTO) => Promise<void>;
}

export const useOpportunitiesStore = create<OpportunitiesState>((set) => ({
  opportunities: [],
  userApplications: [],
  isLoading: false,
  error: null,

  /**
   * Récupère les opportunités, avec filtre optionnel par type.
   */
  fetchOpportunities: async (type: OpportunityType | 'ALL' = 'ALL') => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const params: Record<string, string> = {};
      if (type !== 'ALL') params.type = type;

      const response = await apiClient.get(API_ENDPOINTS.opportunities.list, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        params,
      });

      set({ opportunities: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des opportunités',
        isLoading: false,
      });
    }
  },

  /**
   * Postule à une opportunité.
   * On attend un champ coverLetter dans le corps de la requête.
   */
  applyToOpportunity: async (opportunityId: string, coverLetter: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.post(
        API_ENDPOINTS.opportunities.apply(opportunityId),
        { opportunity_id: opportunityId, cover_letter: coverLetter },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      // Mise à jour locale : ajout de la candidature à userApplications
      const newApplication: OpportunityApplication = response.data;
      set((state) => ({
        userApplications: [...state.userApplications, newApplication],
      }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la candidature',
      });
    }
  },

  /**
   * Crée une nouvelle opportunité.
   * L'utilisateur doit être admin ou enseignant selon les règles RBAC (non géré ici).
   */
  createOpportunity: async (data: OpportunityCreateDTO) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.post(
        API_ENDPOINTS.opportunities.create,
        data,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      const newOpportunity: Opportunity = response.data;
      set((state) => ({
        opportunities: [newOpportunity, ...state.opportunities],
      }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la création de l\'opportunité',
      });
    }
  },
}));