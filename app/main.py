"""FastAPI server for home automation system."""
import asyncio
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import config
from app.db.database import db
from app.db.seed_data import seed_database
from app.schemas.responses import StatsResponse
from app.utils.websocket_manager import ws_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan (startup and shutdown)."""
    # Startup
    print("Starting home automation server...")
    await db.connect()
    await db.initialize_schema()
    await seed_database(db)
    print(f"Database initialized at: {config.DATABASE_PATH}")
    
    # Start background task for database polling
    polling_task = asyncio.create_task(poll_database_changes())
    
    yield
    
    # Shutdown
    print("Shutting down home automation server...")
    polling_task.cancel()
    try:
        await polling_task
    except asyncio.CancelledError:
        pass
    await db.disconnect()


app = FastAPI(
    title="Home Automation API",
    description="REST API and WebSocket server for home automation control",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Background task to poll for database changes
async def poll_database_changes():
    """Poll database for changes and broadcast to WebSocket clients."""
    last_update_time = None
    last_mode = None
    
    print("Starting database change polling (checks every 100ms)...")
    
    while True:
        try:
            await asyncio.sleep(config.UPDATE_CHECK_INTERVAL)
            
            # Check if there are any WebSocket connections
            if not ws_manager.active_connections:
                continue
            
            # Get the most recent update time from devices table
            async with db._connection.execute(
                "SELECT MAX(last_updated) as max_time FROM devices"
            ) as cursor:
                row = await cursor.fetchone()
                current_update_time = row[0] if row else None
            
            # Check for home mode changes
            current_mode = await db.get_active_mode()
            
            # If database has been updated, broadcast changes
            if last_update_time is not None and current_update_time != last_update_time:
                print(f"📡 Database change detected! Broadcasting to {len(ws_manager.active_connections)} clients...")
                
                # Broadcast full refresh to all clients
                await ws_manager.broadcast_full_refresh()
                
                # Update last known time
                last_update_time = current_update_time
            elif last_update_time is None:
                # First run - just store the timestamp
                last_update_time = current_update_time
            
            # Check for mode changes
            if last_mode is not None and current_mode != last_mode:
                print(f"🏠 Home mode changed to: {current_mode}")
                await ws_manager.broadcast_mode_change(current_mode)
                last_mode = current_mode
            elif last_mode is None:
                last_mode = current_mode
                    
        except asyncio.CancelledError:
            print("Stopping database polling...")
            break
        except Exception as e:
            print(f"Error in database polling: {e}")
            import traceback
            traceback.print_exc()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Home Automation API",
        "version": "1.0.0",
        "endpoints": {
            "devices": "/api/devices",
            "rooms": "/api/rooms",
            "stats": "/api/stats",
            "websocket": "/ws"
        }
    }


@app.get("/api/devices")
async def get_devices(room: Optional[str] = None, type: Optional[str] = None):
    """Get all devices with optional filters."""
    devices = await db.get_devices(room=room, device_type=type)
    return devices


@app.get("/api/rooms")
async def get_rooms():
    """Get list of unique rooms."""
    rooms = await db.get_rooms()
    return rooms


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics."""
    stats = await db.get_stats()
    return stats


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)
    
    try:
        # Send initial data
        devices = await db.get_devices()
        await websocket.send_json({
            "type": "initial_data",
            "devices": devices
        })
        
        # Keep connection alive and listen for messages
        while True:
            # We mostly broadcast from server to client
            # But we can receive messages if needed
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Process incoming messages if needed
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "ping"})
                
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level="info"
    )
