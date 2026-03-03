"""Socket.IO WebSocket handler — Real-time event broadcasting."""
import json
import logging
import socketio

logger = logging.getLogger("nexus.websocket")


def create_sio():
    """Create and configure Socket.IO async server."""
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",
        logger=False,
        engineio_logger=False,
    )

    @sio.event
    async def connect(sid, environ):
        logger.info(f"[WS] Client connected: {sid}")
        await sio.emit("connection_ack", {
            "status": "connected",
            "message": "NEXUS-GOV Command Center — Connection established",
        }, room=sid)

    @sio.event
    async def disconnect(sid):
        logger.info(f"[WS] Client disconnected: {sid}")

    @sio.event
    async def ping(sid, data):
        await sio.emit("pong", {"timestamp": data.get("timestamp", 0)}, room=sid)

    @sio.event
    async def request_state(sid, data):
        """Client requests full state sync."""
        logger.info(f"[WS] State sync requested by {sid}")
        # Will be handled by the broadcast function

    return sio


async def broadcast(sio: socketio.AsyncServer, event: str, data: dict):
    """Broadcast an event to all connected clients."""
    try:
        await sio.emit(event, data)
    except Exception as e:
        logger.error(f"[WS] Broadcast error: {e}")
