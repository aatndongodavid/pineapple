# backend/src/shared_kernel/infrastructure/websocket_pubsub.py

import asyncio
import json
import logging
from typing import Dict, Set
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger("pineapple.ws")


class ConnectionManager:
    """Gestionnaire de connexions WebSocket locales et synchronisation Pub/Sub Redis."""

    def __init__(self):
        # Dict[conversation_id, Set[WebSocket]]
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        self.active_connections[conversation_id].add(websocket)

    def disconnect(self, conversation_id: str, websocket: WebSocket):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].discard(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast_to_local(self, conversation_id: str, message_data: dict):
        """Diffuser un message aux clients WebSocket locaux."""
        if conversation_id in self.active_connections:
            dead_sockets = set()
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message_data)
                except Exception as e:
                    logger.warning(f"Error sending WS message: {e}")
                    dead_sockets.add(connection)
            for dead in dead_sockets:
                self.active_connections[conversation_id].discard(dead)


ws_manager = ConnectionManager()
