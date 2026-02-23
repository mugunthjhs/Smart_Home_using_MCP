"""API response schemas."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.device import Device


class DevicesResponse(BaseModel):
    """Response for device list."""
    devices: List[Device] = []


class RoomsResponse(BaseModel):
    """Response for room list."""
    rooms: List[str] = []


class LightStats(BaseModel):
    """Light statistics."""
    on: int = 0
    total: int = 0


class DoorStats(BaseModel):
    """Door/lock statistics."""
    locked: int = 0
    total: int = 0


class StatsResponse(BaseModel):
    """Dashboard statistics response."""
    lights: LightStats
    doors: DoorStats
    total_devices: int
    garage_open: bool = False
    active_mode: Optional[str] = None


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # device_update, mode_change, full_refresh
    device_id: Optional[str] = None
    room: Optional[str] = None
    device_type: Optional[str] = None
    state: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    mode: Optional[str] = None
