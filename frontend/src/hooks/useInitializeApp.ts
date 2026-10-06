// frontend/src/hooks/useInitializeApp.ts

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store/authStore';
import { useOfflineSyncStore } from '@/lib/store/offlineSyncStore';
import { useWebSocket } from '@/lib/websocket/client';
import apiClient from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';

/**
 * Hook d'initialisation global de l'application.
 * Il est appelé une seule fois au montage de App.tsx.
 * Responsabilités :
 * - Vérifier le token JWT et recharger le profil utilisateur.
 * - Initialiser la connexion WebSocket (écoute des notifications).
 * - Déclencher la synchronisation des actions hors‑ligne si le réseau est disponible.
 * Retourne `isInitialized` pour retarder le rendu des routes tant que les vérifications ne sont pas terminées.
 */
export function useInitializeApp(): boolean {
  const [isInitialized, setIsInitialized] = useState(false);
  const { token, setAuthData, logout } = useAuthStore();

  // Initialisation du WebSocket global
  useWebSocket({
    onMessage: (message) => {
      console.log('[WebSocket] Message reçu :', message);
    },
  });

  useEffect(() => {
    let isMounted = true;

    async function initialize() {
      if (token) {
        try {
          const response = await apiClient.get(API_ENDPOINTS.identity.me);
          const meData = response.data;
          setAuthData(token, meData);
        } catch (error) {
          logout();
        }
      }

      if (navigator.onLine) {
        useOfflineSyncStore.getState().syncActions();
      }

      if (isMounted) {
        setIsInitialized(true);
      }
    }

    initialize();

    return () => {
      isMounted = false;
    };
  }, [token, setAuthData, logout]);

  return isInitialized;
}