// frontend/src/lib/store/democracyStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types (alignés sur les DTOs backend)
// ---------------------------------------------------------------------------
export type ElectionStatus =
  | 'DRAFT'
  | 'CAMPAIGN'
  | 'VOTING_OPEN'
  | 'VOTING_CLOSED'
  | 'RESULTS_PUBLISHED'
  | 'ARCHIVED';

export interface ElectionResponseDTO {
  id: string;
  tenant_id: string;
  title: string;
  election_type: string;
  status: ElectionStatus;
  eligibility_rules: Record<string, unknown>;
  voting_start_at: string;
  voting_end_at: string;
  total_voters_count: number;
}

export interface SystemHealthData {
  infrastructure: 'HEALTHY' | 'DEGRADED' | 'DOWN';
  api: 'OPERATIONAL' | 'DEGRADED';
  database: 'OPERATIONAL' | 'DEGRADED';
  voteEngine: 'READY' | 'NOT_READY';
  storage: 'OPERATIONAL' | 'DEGRADED';
  eligibleVoters: number;
  participants: number;
  participationRate: number;
}

// ---------------------------------------------------------------------------
// Store Zustand
// ---------------------------------------------------------------------------
interface DemocracyState {
  activeElections: ElectionResponseDTO[];
  currentElection: ElectionResponseDTO | null;
  systemHealth: SystemHealthData | null;
  isVoting: boolean;
  hasVoted: boolean;
  error: string | null;

  fetchElections: (tenantId: string) => Promise<void>;
  getElectionDetails: (electionId: string, tenantId: string) => Promise<void>;
  castVote: (electionId: string, choiceId: string) => Promise<void>;
  fetchAuditLedger: (electionId: string) => Promise<any>; // Retourne les données brutes
}

export const useDemocracyStore = create<DemocracyState>((set) => ({
  activeElections: [],
  currentElection: null,
  systemHealth: null,
  isVoting: false,
  hasVoted: false,
  error: null,

  /**
   * Récupère la liste des élections du campus.
   */
  fetchElections: async (tenantId: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      if (!token) throw new Error('Non authentifié');

      const response = await apiClient.get(API_ENDPOINTS.democracy.elections, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });
      set({ activeElections: response.data });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des élections',
      });
    }
  },

  /**
   * Charge les détails d'une élection précise.
   */
  getElectionDetails: async (electionId: string, tenantId: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      if (!token) throw new Error('Non authentifié');

      const response = await apiClient.get(
        `${API_ENDPOINTS.democracy.elections}/${electionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      set({ currentElection: response.data });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la récupération de l\'élection',
      });
    }
  },

  /**
   * Soumet un bulletin de vote. Gère spécifiquement le conflit HTTP 409 (déjà voté).
   */
  castVote: async (electionId: string, choiceId: string) => {
    set({ isVoting: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const payload = {
        election_id: electionId,
        choice_id: choiceId,
      };

      await apiClient.post(
        `${API_ENDPOINTS.democracy.elections}/${electionId}/vote`,
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      set({ hasVoted: true });
    } catch (err: any) {
      if (err.response?.status === 409) {
        set({
          hasVoted: true,
          error: 'Vous avez déjà voté pour cette élection.',
        });
      } else {
        set({
          error: err.response?.data?.detail || 'Erreur lors du vote',
        });
      }
    } finally {
      set({ isVoting: false });
    }
  },

  /**
   * Récupère le registre d'audit de l'élection.
   */
  fetchAuditLedger: async (electionId: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get(
        `${API_ENDPOINTS.democracy.elections}/${electionId}/audit`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      return response.data;
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement de l\'audit',
      });
      return null;
    }
  },
}));