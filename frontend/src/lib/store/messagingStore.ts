// frontend/src/lib/store/messagingStore.ts

import { create } from 'zustand';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import { useAuthStore } from './authStore';
import { useTenantStore } from './tenantStore';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export interface ConversationDTO {
  id: string;
  tenant_id: string;
  participant_ids: string[];
  context_type?: string | null;
  context_id?: string | null;
  last_message_at?: string | null;
  // Champs additionnels pour l'affichage
  contactName?: string;
  contextLabel?: string;
  unreadCount?: number;
}

export interface MessageDTO {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  message_type: 'TEXT' | 'IMAGE' | 'LOCATION' | 'SYSTEM';
  sent_at: string;
  status?: 'sending' | 'sent' | 'delivered' | 'read';
}

interface MessagingState {
  conversations: ConversationDTO[];
  activeConversationId: string | null;
  messages: Record<string, MessageDTO[]>;
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  error: string | null;

  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => Promise<void>;
  receiveWebSocketMessage: (message: MessageDTO) => void;
  setActiveConversation: (conversationId: string | null) => void;
}

export const useMessagingStore = create<MessagingState>((set, get) => ({
  conversations: [],
  activeConversationId: null,
  messages: {},
  isLoadingConversations: false,
  isLoadingMessages: false,
  error: null,

  /**
   * Charge la liste des conversations de l'utilisateur.
   */
  fetchConversations: async () => {
    set({ isLoadingConversations: true, error: null });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get('/api/v1/messaging/conversations', {
        headers: {
          Authorization: `Bearer ${token}`,
          'X-Tenant-ID': tenantId,
        },
      });

      set({ conversations: response.data, isLoadingConversations: false });
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des conversations',
        isLoadingConversations: false,
      });
    }
  },

  /**
   * Charge les messages d'une conversation spécifique.
   */
  fetchMessages: async (conversationId: string) => {
    set({ isLoadingMessages: true, error: null, activeConversationId: conversationId });
    try {
      const token = useAuthStore.getState().token;
      const tenantId = useTenantStore.getState().tenantId;
      if (!token || !tenantId) throw new Error('Session invalide');

      const response = await apiClient.get(
        API_ENDPOINTS.campusLife.messages(conversationId),
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      set((state) => ({
        messages: {
          ...state.messages,
          [conversationId]: response.data,
        },
        isLoadingMessages: false,
      }));
    } catch (err: any) {
      set({
        error: err.response?.data?.detail || 'Erreur lors du chargement des messages',
        isLoadingMessages: false,
      });
    }
  },

  /**
   * Envoie un message et l'ajoute localement.
   */
  sendMessage: async (conversationId: string, content: string) => {
    const token = useAuthStore.getState().token;
    const tenantId = useTenantStore.getState().tenantId;
    if (!token || !tenantId) throw new Error('Session invalide');

    const currentUser = useAuthStore.getState().user;
    const tempMessage: MessageDTO = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      sender_id: currentUser?.id || '',
      content,
      message_type: 'TEXT',
      sent_at: new Date().toISOString(),
      status: 'sending',
    };

    // Ajout optimiste
    set((state) => ({
      messages: {
        ...state.messages,
        [conversationId]: [...(state.messages[conversationId] || []), tempMessage],
      },
    }));

    try {
      const response = await apiClient.post(
        API_ENDPOINTS.campusLife.sendMessage,
        {
          conversation_id: conversationId,
          content,
          message_type: 'TEXT',
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'X-Tenant-ID': tenantId,
          },
        }
      );

      const savedMessage: MessageDTO = response.data;
      // Remplace le message temporaire par le message sauvegardé
      set((state) => ({
        messages: {
          ...state.messages,
          [conversationId]: state.messages[conversationId].map((msg) =>
            msg.id === tempMessage.id ? savedMessage : msg
          ),
        },
      }));
    } catch (err: any) {
      // En cas d'échec, on pourrait marquer le message comme échoué
      set((state) => ({
        messages: {
          ...state.messages,
          [conversationId]: state.messages[conversationId].map((msg) =>
            msg.id === tempMessage.id ? { ...msg, status: 'sent' } : msg
          ),
        },
        error: err.response?.data?.detail || 'Erreur lors de l\'envoi du message',
      }));
    }
  },

  /**
   * Reçoit un message via WebSocket et met à jour l'état.
   */
  receiveWebSocketMessage: (message: MessageDTO) => {
    set((state) => ({
      messages: {
        ...state.messages,
        [message.conversation_id]: [
          ...(state.messages[message.conversation_id] || []),
          message,
        ],
      },
    }));

    // Si la conversation n'est pas dans la liste, on pourrait la rafraîchir
    const conversationExists = get().conversations.some(
      (conv) => conv.id === message.conversation_id
    );
    if (!conversationExists) {
      // On pourrait déclencher un fetchConversations, mais pour l'exemple on laisse
    }
  },

  /**
   * Définit la conversation active.
   */
  setActiveConversation: (conversationId: string | null) => {
    set({ activeConversationId: conversationId });
  },
}));