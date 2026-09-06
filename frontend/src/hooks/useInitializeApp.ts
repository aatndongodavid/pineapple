// frontend/src/hooks/useInitializeApp.ts

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';
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
  const { token, login, logout } = useAuthStore();
  const { tenantId } = useTenantStore();

  // Initialisation du WebSocket global (le hook vérifie lui‑même la présence du token)
  // On écoute les messages de type notification via un callback vide ou un store dédié.
  useWebSocket({
    onMessage: (message) => {
      // Ici on pourrait dispatcher vers un notificationStore
      console.log('[WebSocket] Message reçu :', message);
    },
  });

  useEffect(() => {
    let isMounted = true;

    async function initialize() {
      // Si un token existe, on tente de recharger le profil utilisateur.
      if (token && tenantId) {
        try {
          const response = await apiClient.get(API_ENDPOINTS.identity.me, {
            headers: {
              Authorization: `Bearer ${token}`,
              'X-Tenant-ID': tenantId,
            },
          });
          const userData = response.data;
          // Mise à jour du store d'authentification avec les données fraîches
          login(
            token,
            {
              id: userData.id,
              email: userData.email,
              firstName: userData.first_name,
              lastName: userData.last_name,
              matricule: userData.matricule,
            },
            userData.campus_status_display
          );
        } catch (error) {
          // Token invalide ou expiré : on déconnecte l'utilisateur.
          logout();
        }
      }

      // Déclencher la synchronisation des actions hors‑ligne si le réseau est disponible.
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
  }, [token, tenantId, login, logout]);

  return isInitialized;
}