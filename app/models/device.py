"""Device models and types."""
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Device types
DeviceType = Literal[
    "light",
    "fan",
    "blinds",
    "thermostat",
    "lock",
    "garage",
    "temperature_sensor",
    "motion_sensor",
    "sprinkler",
    "ev_charger",
    "fish_feeder"
]

# Device states
DeviceState = Literal[
    "on", "off",
    "open", "closed", "partial",
    "locked", "unlocked",
    "active", "idle",
    "motion", "no_motion",
    "charging", "feeding",
    "heat", "cool", "auto"
]


class Device(BaseModel):
    """Device model."""
    id: str
    type: DeviceType
    room: Optional[str] = None
    state: DeviceState
    properties: Dict[str, Any] = Field(default_factory=dict)
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "living_room_light_main",
                "type": "light",
                "room": "living_room",
                "state": "on",
                "properties": {"brightness": 75, "color_temp": 3000},
                "last_updated": "2024-01-01T12:00:00"
            }
        }


class DeviceUpdate(BaseModel):
    """Device update payload."""
    state: Optional[DeviceState] = None
    properties: Optional[Dict[str, Any]] = None


class Event(BaseModel):
    """Event log model."""
    id: Optional[int] = None
    event_type: str
    device_id: Optional[str] = None
    action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
