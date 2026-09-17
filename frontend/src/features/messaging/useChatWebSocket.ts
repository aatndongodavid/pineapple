import { useState, useEffect, useCallback, useRef } from 'react';
import { MessageData } from './MessageBubble';

interface UseChatWebSocketReturn {
    messages: MessageData[];
    sendMessage: (content: string) => void;
    isConnected: boolean;
}

export function useChatWebSocket(roomId: string, currentUserId: string): UseChatWebSocketReturn {
    const [messages, setMessages] = useState<MessageData[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        // En production, l'URL sera dynamique via les variables d'environnement
        const wsUrl = `ws://localhost:8000/api/v1/chat/ws/${roomId}`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setIsConnected(true);
        };

        ws.onmessage = (event) => {
            const data = event.data;
            const newMessage: MessageData = {
                id: `msg-${Date.now()}-${Math.random()}`,
                senderId: 'system', // ou l'ID de l'envoyeur reçu du backend
                content: data,
                timestamp: new Date().toISOString(),
                status: 'delivered'
            };
            setMessages(prev => [...prev, newMessage]);
        };

        ws.onclose = () => {
            setIsConnected(false);
        };

        wsRef.current = ws;

        return () => {
            ws.close();
        };
    }, [roomId]);

    const sendMessage = useCallback((content: string) => {
        if (wsRef.current && isConnected) {
            wsRef.current.send(content);
            // On peut ajouter le message localement en attente
            const localMessage: MessageData = {
                id: `msg-local-${Date.now()}`,
                senderId: currentUserId,
                content,
                timestamp: new Date().toISOString(),
                status: 'sent'
            };
            setMessages(prev => [...prev, localMessage]);
        }
    }, [isConnected, currentUserId]);

    return { messages, sendMessage, isConnected };
}
