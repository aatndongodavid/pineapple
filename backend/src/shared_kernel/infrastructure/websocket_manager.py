# backend/src/shared_kernel/infrastructure/websocket_manager.py

import json
import uuid
from typing import Dict, List, Set
from fastapi import WebSocket


class RoomAvailabilityWebSocketManager:
    """
    Gestionnaire de connexions WebSocket temps réel pour la diffusion
    des états de disponibilité des salles par établissement (tenant).
    """

    def __init__(self):
        # Map: tenant_id -> Set[WebSocket]
        self._active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, tenant_id: str, websocket: WebSocket):
        await websocket.accept()
        if tenant_id not in self._active_connections:
            self._active_connections[tenant_id] = set()
        self._active_connections[tenant_id].add(websocket)

    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self._active_connections:
            self._active_connections[tenant_id].discard(websocket)
            if not self._active_connections[tenant_id]:
                del self._active_connections[tenant_id]

    async def broadcast_room_status_change(self, tenant_id: str, payload: dict):
        """
        Diffuse un événement de mise à jour de statut de salle à tous les abonnés du tenant.
        """
        connections = self._active_connections.get(tenant_id, set())
        if not connections:
            return

        message = json.dumps(payload)
        to_remove = set()
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.add(ws)

        for ws in to_remove:
            self.disconnect(tenant_id, ws)


# Instance globale partagée
room_ws_manager = RoomAvailabilityWebSocketManager()


class NotificationWebSocketManager:
    """
    Gestionnaire WebSocket pour la livraison temps réel des notifications In-App ciblées par utilisateur et tenant.
    """

    def __init__(self):
        # Map: (tenant_id, user_id) -> Set[WebSocket]
        self._user_connections: Dict[str, Set[WebSocket]] = {}

    def _key(self, tenant_id: str, user_id: str) -> str:
        return f"{tenant_id}:{user_id}"

    async def connect(self, tenant_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        key = self._key(tenant_id, user_id)
        if key not in self._user_connections:
            self._user_connections[key] = set()
        self._user_connections[key].add(websocket)

    def disconnect(self, tenant_id: str, user_id: str, websocket: WebSocket):
        key = self._key(tenant_id, user_id)
        if key in self._user_connections:
            self._user_connections[key].discard(websocket)
            if not self._user_connections[key]:
                del self._user_connections[key]

    async def send_user_notification(self, tenant_id: str, user_id: str, payload: dict):
        key = self._key(tenant_id, user_id)
        connections = self._user_connections.get(key, set())
        if not connections:
            return

        message = json.dumps(payload)
        to_remove = set()
        for ws in connections:
            try:
                await ws.send_text(message)
            except Exception:
                to_remove.add(ws)

        for ws in to_remove:
            self.disconnect(tenant_id, user_id, ws)


notification_ws_manager = NotificationWebSocketManager()
