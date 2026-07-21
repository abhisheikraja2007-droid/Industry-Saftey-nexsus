"""
WebSocket endpoint handler.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from websocket.ws_manager import ws_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    # Send initial ping
    await ws_manager.send_personal(ws, {
        "type":    "connected",
        "payload": {"message": "Industrial Safety AI connected", "clients": ws_manager.connection_count},
        "ts":      datetime.now(timezone.utc).isoformat(),
    })
    try:
        while True:
            # Keep alive — listen for client pings
            data = await ws.receive_text()
            if data == "ping":
                await ws_manager.send_personal(ws, {"type": "pong", "ts": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
