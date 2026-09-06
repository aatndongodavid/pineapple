// frontend/src/lib/store/offlineSyncStore.ts

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '@/lib/api/client';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export type QueuedActionType =
  | 'like_post'
  | 'unlike_post'
  | 'send_message'
  | 'create_post';

export interface QueuedAction {
  id: string;             // identifiant unique (généré)
  type: QueuedActionType;
  payload: any;           // données variables selon le type
  createdAt: string;      // ISO string
}

interface OfflineSyncState {
  actionQueue: QueuedAction[];
  isSyncing: boolean;

  queueAction: (type: QueuedActionType, payload: any) => void;
  syncActions: () => Promise<void>;
  clearQueue: () => void;
}

// ---------------------------------------------------------------------------
// Helper pour générer un identifiant unique
// ---------------------------------------------------------------------------
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// ---------------------------------------------------------------------------
// Store Zustand persistant
// ---------------------------------------------------------------------------
export const useOfflineSyncStore = create<OfflineSyncState>()(
  persist(
    (set, get) => ({
      actionQueue: [],
      isSyncing: false,

      /**
       * Ajoute une action à la file d'attente.
       */
      queueAction: (type, payload) => {
        const action: QueuedAction = {
          id: generateId(),
          type,
          payload,
          createdAt: new Date().toISOString(),
        };
        set((state) => ({ actionQueue: [...state.actionQueue, action] }));
      },

      /**
       * Synchronise les actions en attente avec le backend.
       * Elle est déclenchée automatiquement lorsque la connexion revient.
       */
      syncActions: async () => {
        const { actionQueue, isSyncing } = get();
        if (isSyncing || actionQueue.length === 0) return;

        set({ isSyncing: true });
        const token = useAuthStore.getState().token;
        const tenantId = useTenantStore.getState().tenantId;

        if (!token || !tenantId) {
          // On ne peut pas synchroniser sans session
          set({ isSyncing: false });
          return;
        }

        // Copie de la file pour itérer sans mutation pendant le traitement
        const pendingActions = [...actionQueue];
        const successfulIds: string[] = [];

        for (const action of pendingActions) {
          try {
            let endpoint = '';
            let method: 'post' | 'delete' = 'post';
            let body: any = action.payload;

            switch (action.type) {
              case 'like_post':
                endpoint = `/api/v1/community/posts/${action.payload.postId}/like`;
                method = 'post';
                break;
              case 'unlike_post':
                endpoint = `/api/v1/community/posts/${action.payload.postId}/like`;
                method = 'delete';
                break;
              case 'send_message':
                endpoint = '/api/v1/campus-life/messages';
                method = 'post';
                body = {
                  conversation_id: action.payload.conversationId,
                  content: action.payload.content,
                  message_type: 'TEXT',
                };
                break;
              case 'create_post':
                endpoint = '/api/v1/community/posts';
                method = 'post';
                break;
              default:
                continue;
            }

            await apiClient.request({
              url: endpoint,
              method,
              data: body,
              headers: {
                Authorization: `Bearer ${token}`,
                'X-Tenant-ID': tenantId,
              },
            });

            successfulIds.push(action.id);
          } catch (error) {
            // On arrête la synchronisation en cas d'erreur (réseau, 500...)
            // Les actions non traitées restent en file pour un prochain essai.
            break;
          }
        }

        // Retirer les actions réussies
        if (successfulIds.length > 0) {
          set((state) => ({
            actionQueue: state.actionQueue.filter(
              (a) => !successfulIds.includes(a.id)
            ),
          }));
        }

        set({ isSyncing: false });
      },

      clearQueue: () => set({ actionQueue: [] }),
    }),
    {
      name: 'pineapple-offline-sync-storage',
      partialize: (state) => ({ actionQueue: state.actionQueue }),
    }
  )
);

// ---------------------------------------------------------------------------
// Écoute des événements réseau pour déclencher la synchronisation
// ---------------------------------------------------------------------------
if (typeof window !== 'undefined') {
  window.addEventListener('online', () => {
    useOfflineSyncStore.getState().syncActions();
  });
}