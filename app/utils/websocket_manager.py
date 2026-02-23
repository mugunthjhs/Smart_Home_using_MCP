
"""WebSocket connection manager for real-time updates."""
import asyncio
import json
from typing import List, Dict, Any
from fastapi import WebSocket
from datetime import datetime


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._update_flag = asyncio.Event()
        self._update_data: Dict[str, Any] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients."""
        if not self.active_connections:
            return
        
        message_text = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_text)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_device_update(
        self,
        device_id: str = None,
        room: str = None,
        device_type: str = None,
        state: str = None,
        properties: Dict[str, Any] = None
    ):
        """Broadcast a device update message."""
        message = {
            "type": "device_update",
            "device_id": device_id,
            "room": room,
            "device_type": device_type,
            "state": state,
            "properties": properties,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_mode_change(self, mode: str):
        """Broadcast a home mode change."""
        message = {
            "type": "mode_change",
            "mode": mode,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    async def broadcast_full_refresh(self):
        """Broadcast a full refresh signal."""
        message = {
            "type": "full_refresh",
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast(message)
    
    def signal_update(self, update_data: Dict[str, Any] = None):
        """Signal that an update has occurred (for polling mechanism)."""
        self._update_data = update_data or {}
        self._update_flag.set()
    
    async def wait_for_update(self, timeout: float = None):
        """Wait for an update signal (for polling mechanism)."""
        try:
            await asyncio.wait_for(self._update_flag.wait(), timeout=timeout)
            self._update_flag.clear()
            return self._update_data
        except asyncio.TimeoutError:
            return None


# Global WebSocket manager instance
ws_manager = WebSocketManager()
