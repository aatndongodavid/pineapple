// frontend/src/lib/store/feedStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// Types (alignés sur les DTOs backend)
export type AudienceScope = 'LOCAL' | 'EXTENDED' | 'SPONSORED' | 'PUBLIC';
export type PostType = 'TEXT' | 'IMAGE' | 'VIDEO' | 'EVENT' | 'PROJECT';

export interface PostResponseDTO {
  id: string;
  tenant_id: string;
  author_id: string;
  organization_id?: string | null;
  content: string;
  post_type: PostType;
  media_urls: string[];
  scope: AudienceScope;
  is_sponsored: boolean;
  views_count: number;
  created_at: string;
  // Champ additionnel pour le like optimiste
  likes_count?: number;
}

export interface PostCreateDTO {
  content: string;
  post_type: PostType;
  media_urls: string[];
  organization_id?: string | null;
  scope: AudienceScope;
}

interface FeedState {
  posts: PostResponseDTO[];
  activeTab: string;
  isLoading: boolean;
  error: string | null;
  fetchFeed: (tenantId: string, tab: string) => Promise<void>;
  createPost: (data: PostCreateDTO) => Promise<void>;
  likePost: (postId: string) => void;
}

export const useFeedStore = create<FeedState>((set, get) => ({
  posts: [],
  activeTab: 'pour_toi',
  isLoading: false,
  error: null,

  fetchFeed: async (tenantId: string, tab: string) => {
    set({ isLoading: true, error: null, activeTab: tab });
    try {
      const { token } = useAuthStore.getState();
      if (!token) throw new Error('Non authentifié');

      const response = await apiClient.get(API_ENDPOINTS.community.feed, {
        params: { tab },
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      set({ posts: response.data, isLoading: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement du fil',
        isLoading: false,
      });
    }
  },

  createPost: async (data: PostCreateDTO) => {
    set({ error: null });
    try {
      const { token } = useAuthStore.getState();
      const { tenantId } = useTenantStore.getState();
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.post(API_ENDPOINTS.community.posts, data, {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      const newPost: PostResponseDTO = response.data;
      // Insertion en tête de liste (optimiste)
      set((state) => ({ posts: [newPost, ...state.posts] }));
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Erreur lors de la publication' });
    }
  },

  likePost: (postId: string) => {
    // Mise à jour optimiste locale (à brancher sur un endpoint ultérieurement)
    set((state) => ({
      posts: state.posts.map((post) =>
        post.id === postId
          ? { ...post, likes_count: (post.likes_count || 0) + 1 }
          : post
      ),
    }));
  },
}));