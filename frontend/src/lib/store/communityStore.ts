// frontend/src/lib/store/communityStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// Types simplifiés (à adapter selon les DTOs backend)
export interface OrganizationResponseDTO {
  id: string;
  tenant_id: string;
  name: string;
  slug: string;
  description: string;
  type: string;
  logo_url?: string | null;
  is_verified: boolean;
  owner_user_id: string;
}

export interface RoomResponseDTO {
  id: string;
  tenant_id: string;
  name: string;
  building: string;
  status: 'FREE' | 'OCCUPIED' | 'TO_CONFIRM';
  declared_by_user_id: string;
  expires_at: string | null;
}

interface CommunityState {
  organizations: OrganizationResponseDTO[];
  rooms: RoomResponseDTO[];
  isLoading: boolean;
  error: string | null;
  fetchOrganizations: (tenantId: string) => Promise<void>;
  fetchRooms: (tenantId: string) => Promise<void>;
  declareRoomStatus: (
    roomId: string,
    status: string,
    durationMinutes: number
  ) => Promise<void>;
}

export const useCommunityStore = create<CommunityState>((set, get) => ({
  organizations: [],
  rooms: [],
  isLoading: false,
  error: null,

  fetchOrganizations: async (tenantId: string) => {
    set({ isLoading: true, error: null });
    try {
      const { token } = useAuthStore.getState();
      if (!token) throw new Error('Non authentifié');

      const response = await apiClient.get(API_ENDPOINTS.community.organizations, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      set({ organizations: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des organisations',
        isLoading: false,
      });
    }
  },

  fetchRooms: async (tenantId: string) => {
    set({ isLoading: true, error: null });
    try {
      const { token } = useAuthStore.getState();
      if (!token) throw new Error('Non authentifié');

      const response = await apiClient.get(API_ENDPOINTS.community.rooms, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      set({ rooms: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des salles',
        isLoading: false,
      });
    }
  },

  declareRoomStatus: async (roomId: string, status: string, durationMinutes: number) => {
    const { token } = useAuthStore.getState();
    const { tenantId } = useTenantStore.getState();
    if (!token || !tenantId) throw new Error('Session invalide');

    // Sauvegarde de l'état antérieur pour rollback éventuel
    const previousRooms = get().rooms;

    // Mise à jour optimiste : on modifie immédiatement la salle localement
    set((state) => ({
      rooms: state.rooms.map((room) =>
        room.id === roomId
          ? {
              ...room,
              status: status as RoomResponseDTO['status'],
              expires_at:
                status === 'FREE'
                  ? new Date(Date.now() + durationMinutes * 60 * 1000).toISOString()
                  : null,
            }
          : room
      ),
    }));

    try {
      await apiClient.post(
        API_ENDPOINTS.community.declareRoom,
        {
          room_id: roomId,
          status,
          validity_minutes: durationMinutes,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );
      // Si succès, on peut éventuellement refetch pour être sûr, mais on garde l'optimiste
    } catch (err: any) {
      // Rollback en cas d'échec
      set({ rooms: previousRooms });
      throw new Error(err.response?.data?.detail || 'Erreur lors de la déclaration');
    }
  },
}));