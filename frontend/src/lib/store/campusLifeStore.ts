// frontend/src/lib/store/campusLifeStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export type ListingCategory = 'BOOKS' | 'ELECTRONICS' | 'CLOTHING' | 'SERVICES' | 'HOUSING' | 'OTHER';
export type ListingStatus = 'ACTIVE' | 'RESERVED' | 'SOLD' | 'ARCHIVED';

export interface Listing {
  id: string;
  tenant_id: string;
  seller_id: string;
  title: string;
  description: string;
  price_fcfa: number;
  category: ListingCategory;
  status: ListingStatus;
  image_urls: string[];
  created_at: string;
}

export interface ListingCreateDTO {
  title: string;
  description: string;
  price_fcfa: number;
  category: ListingCategory;
  image_urls?: string[];
}

export type RideStatus = 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface Ride {
  id: string;
  tenant_id: string;
  driver_id: string;
  departure_name: string;
  destination_name: string;
  departure_time: string;
  total_seats: number;
  available_seats: number;
  price_per_seat_fcfa: number;
  passenger_ids: string[];
  status: RideStatus;
}

export interface RideCreateDTO {
  departure_name: string;
  destination_name: string;
  departure_time: string;
  total_seats: number;
  price_per_seat_fcfa: number;
}

export interface RideSearchParams {
  departure?: string;
  destination?: string;
}

interface CampusLifeState {
  listings: Listing[];
  rides: Ride[];
  isLoading: boolean;
  error: string | null;

  fetchListings: (category?: ListingCategory | 'ALL') => Promise<void>;
  createListing: (data: ListingCreateDTO) => Promise<void>;
  fetchRides: (searchParams?: RideSearchParams) => Promise<void>;
  proposeRide: (data: RideCreateDTO) => Promise<void>;
  bookRideSeat: (rideId: string) => Promise<void>;
}

export const useCampusLifeStore = create<CampusLifeState>((set) => ({
  listings: [],
  rides: [],
  isLoading: false,
  error: null,

  // --- Marketplace ---
  fetchListings: async (category: ListingCategory | 'ALL' = 'ALL') => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const params: Record<string, string> = {};
      if (category !== 'ALL') params.category = category;

      const response = await apiClient.get(API_ENDPOINTS.campusLife.marketplace, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        params,
      });

      set({ listings: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des annonces',
        isLoading: false,
      });
    }
  },

  createListing: async (data: ListingCreateDTO) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.post(API_ENDPOINTS.campusLife.marketplace, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      const newListing: Listing = response.data;
      set((state) => ({ listings: [newListing, ...state.listings] }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la création de l\'annonce',
      });
    }
  },

  // --- Pineapple Ride ---
  fetchRides: async (searchParams: RideSearchParams = {}) => {
    set({ isLoading: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const params: Record<string, string> = {};
      if (searchParams.departure) params.departure = searchParams.departure;
      if (searchParams.destination) params.destination = searchParams.destination;

      const response = await apiClient.get(API_ENDPOINTS.campusLife.rides, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
        params,
      });

      set({ rides: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des trajets',
        isLoading: false,
      });
    }
  },

  proposeRide: async (data: RideCreateDTO) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.post(API_ENDPOINTS.campusLife.rides, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      const newRide: Ride = response.data;
      set((state) => ({ rides: [newRide, ...state.rides] }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la proposition du trajet',
      });
    }
  },

  bookRideSeat: async (rideId: string) => {
    set({ error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      await apiClient.post(
        API_ENDPOINTS.campusLife.bookRide(rideId),
        {},
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      // Mise à jour locale (décrémenter available_seats et ajouter l'utilisateur)
      // Note : on pourrait refetch les rides, mais pour l'optimisme on modifie localement
      set((state) => ({
        rides: state.rides.map((ride) =>
          ride.id === rideId
            ? {
                ...ride,
                available_seats: ride.available_seats - 1,
                passenger_ids: [...ride.passenger_ids, useAuthStore.getState().user?.id || ''],
              }
            : ride
        ),
      }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors de la réservation de la place',
      });
    }
  },
}));