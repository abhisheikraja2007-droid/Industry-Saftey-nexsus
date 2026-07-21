"""
WebSocket connection manager.
Maintains a pool of active connections and broadcasts real-time updates.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        logger.info(f"WS client connected. Total: {len(self.active)}")

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)
        logger.info(f"WS client disconnected. Total: {len(self.active)}")

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all active connections."""
        if not self.active:
            return
        data = json.dumps(message, default=str)
        dead = set()
        for ws in self.active.copy():
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.warning(f"WS send failed: {e} — removing client.")
                dead.add(ws)
        for ws in dead:
            self.active.discard(ws)

    async def send_personal(self, ws: WebSocket, message: Dict[str, Any]) -> None:
        """Send a message to a specific client."""
        try:
            await ws.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Personal WS send failed: {e}")
            self.active.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self.active)


# Singleton
ws_manager = ConnectionManager()


def get_ws_manager() -> ConnectionManager:
    return ws_manager
