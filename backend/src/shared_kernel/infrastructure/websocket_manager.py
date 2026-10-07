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
