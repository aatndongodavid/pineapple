// frontend/src/lib/websocket/client.ts

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/lib/store/authStore';
import { useTenantStore } from '@/lib/store/tenantStore';

// ---------------------------------------------------------------------------
// Types des messages
// ---------------------------------------------------------------------------
export interface ElectionHealthUpdate {
  type: 'ELECTION_HEALTH_UPDATE';
  payload: {
    electionId: string;
    infrastructure: 'HEALTHY' | 'DEGRADED' | 'DOWN';
    api: 'OPERATIONAL' | 'DEGRADED';
    database: 'OPERATIONAL' | 'DEGRADED';
    voteEngine: 'READY' | 'NOT_READY';
    storage: 'OPERATIONAL' | 'DEGRADED';
    eligibleVoters: number;
    participants: number;
    participationRate: number;
  };
}

export interface FeedNewPost {
  type: 'FEED_NEW_POST';
  payload: {
    postId: string;
    tenantId: string;
    authorId: string;
    content: string;
    createdAt: string;
  };
}

export interface RoomStatusChange {
  type: 'ROOM_STATUS_CHANGE';
  payload: {
    roomId: string;
    status: 'FREE' | 'OCCUPIED' | 'TO_CONFIRM';
    expiresAt: string | null;
  };
}

export type WsMessage = ElectionHealthUpdate | FeedNewPost | RoomStatusChange;

// ---------------------------------------------------------------------------
// Hook useWebSocket
// ---------------------------------------------------------------------------
interface UseWebSocketOptions {
  url?: string;
  onMessage?: (message: WsMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number; // en ms
  maxReconnectAttempts?: number;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const {
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const shouldReconnectRef = useRef(true);

  const { token } = useAuthStore();
  const { tenantId } = useTenantStore();

  const defaultUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

  const connect = useCallback(() => {
    if (!token || !tenantId) return;

    // Construire l'URL avec query params pour l'authentification et le tenant
    const wsUrl = new URL(url || defaultUrl);
    wsUrl.searchParams.set('token', token);
    wsUrl.searchParams.set('tenant_id', tenantId);

    const socket = new WebSocket(wsUrl.toString());
    wsRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connecté');
      setIsConnected(true);
      reconnectAttemptsRef.current = 0;
      onOpen?.();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WsMessage;
        if (onMessage) {
          onMessage(data);
        }
      } catch (err) {
        console.error('Erreur de parsing WebSocket', err);
      }
    };

    socket.onclose = () => {
      setIsConnected(false);
      onClose?.();
      if (shouldReconnectRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
        const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current); // backoff exponentiel
        reconnectAttemptsRef.current += 1;
        reconnectTimerRef.current = setTimeout(() => {
          if (shouldReconnectRef.current) {
            connect();
          }
        }, delay);
      }
    };

    socket.onerror = (error) => {
      onError?.(error);
      // Fermer le socket en cas d'erreur pour déclencher onclose et éventuelle reconnexion
      socket.close();
    };
  }, [url, token, tenantId, defaultUrl, onOpen, onClose, onError, reconnectInterval, maxReconnectAttempts, onMessage]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket non connecté');
    }
  }, []);

  return { isConnected, sendMessage };
};