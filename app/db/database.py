import json 
import aiosqlite
from pathlib import Path
from typing import Optional,List, Dict ,Any
from datetime import datetime
from app.config import config

class Database:
    def __init__(self,db_path: Path = config.DATABASE_PATH):
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        

    async def connect(self):
        self._connection = await aiosqlite.connect(self.db_path,isolation_level = None)
        self._connection.row_factory = aiosqlite.Row
        await self._connection.execute("PRAGMA journal_model=WAL")

    async def disconnect(self):
        if self._connection:
            await self._connection.close()
            self._connection = None
        
    async def initialize_schema(self):
        schema_path = Path(__file__).parent/"schema.sql"
        with open(schema_path,"r") as f:
            schema_sql = f.read()
        await self._connection.executescript(schema_sql)
        await self._connection.commit()

    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get a single device by ID."""
        async with self._connection.execute(
            "SELECT * FROM devices WHERE id = ?", (device_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None
    
    async def get_devices(
        self, 
        room: Optional[str] = None, 
        device_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get devices with optional filters."""
        query = "SELECT * FROM devices WHERE 1=1"
        params = []
        
        if room:
            query += " AND room = ?"
            params.append(room)
        
        if device_type:
            query += " AND type = ?"
            params.append(device_type)
        
        query += " ORDER BY room, type"
        
        async with self._connection.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_dict(row) for row in rows]
        
    async def update_device(
        self, 
        device_id: str, 
        state: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ):
        """Update device state and/or properties."""
        updates = []
        params = []
        
        if state is not None:
            updates.append("state = ?")
            params.append(state)
        
        if properties is not None:
            updates.append("properties = ?")
            params.append(json.dumps(properties))
        
        if updates:
            updates.append("last_updated = ?")
            params.append(datetime.now().isoformat())
            params.append(device_id)
            
            query = f"UPDATE devices SET {', '.join(updates)} WHERE id = ?"
            await self._connection.execute(query, params)
            await self._connection.commit()
    
    async def log_event(
        self, 
        event_type: str, 
        device_id: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log an event to the events table."""
        await self._connection.execute(
            """INSERT INTO events (event_type, device_id, action, metadata, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (
                event_type,
                device_id,
                action,
                json.dumps(metadata) if metadata else None,
                datetime.now().isoformat()
            )
        )
        await self._connection.commit()

    async def get_rooms(self) -> List[str]:
        """Get list of unique rooms."""
        async with self._connection.execute(
            "SELECT DISTINCT room FROM devices WHERE room IS NOT NULL ORDER BY room"
        ) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_active_mode(self) -> Optional[str]:
        """Get currently active home mode."""
        async with self._connection.execute(
            "SELECT mode FROM home_modes WHERE is_active = 1"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None
        
    async def set_home_mode(self, mode: str):
        """Set active home mode."""
        # Deactivate all modes
        await self._connection.execute("UPDATE home_modes SET is_active = 0")
        
        # Activate selected mode
        await self._connection.execute(
            """UPDATE home_modes 
               SET is_active = 1, last_activated = ? 
               WHERE mode = ?""",
            (datetime.now().isoformat(), mode)
        )
        await self._connection.commit()

    async def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        stats = {
            "lights": {"on": 0, "total": 0},
            "doors": {"locked": 0, "total": 0},
            "total_devices": 0,
            "garage_open": False,
            "active_mode": None
        }
        
        # Count lights
        async with self._connection.execute(
            "SELECT COUNT(*) FROM devices WHERE type = 'light'"
        ) as cursor:
            stats["lights"]["total"] = (await cursor.fetchone())[0]
        
        async with self._connection.execute(
            "SELECT COUNT(*) FROM devices WHERE type = 'light' AND state = 'on'"
        ) as cursor:
            stats["lights"]["on"] = (await cursor.fetchone())[0]
        
        # Count locks
        async with self._connection.execute(
            "SELECT COUNT(*) FROM devices WHERE type = 'lock'"
        ) as cursor:
            stats["doors"]["total"] = (await cursor.fetchone())[0]
        
        async with self._connection.execute(
            "SELECT COUNT(*) FROM devices WHERE type = 'lock' AND state = 'locked'"
        ) as cursor:
            stats["doors"]["locked"] = (await cursor.fetchone())[0]
        
        # Total devices
        async with self._connection.execute(
            "SELECT COUNT(*) FROM devices"
        ) as cursor:
            stats["total_devices"] = (await cursor.fetchone())[0]
        
        # Check garage
        async with self._connection.execute(
            "SELECT state FROM devices WHERE type = 'garage'"
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                stats["garage_open"] = row[0] == "open"
        
        # Active mode
        stats["active_mode"] = await self.get_active_mode()
        
        return stats
    
    def _row_to_dict(self, row: aiosqlite.Row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        data = dict(row)
        # Parse JSON properties
        if data.get("properties"):
            try:
                data["properties"] = json.loads(data["properties"])
            except json.JSONDecodeError:
                data["properties"] = {}
        else:
            data["properties"] = {}
        return data

db = Database()
        