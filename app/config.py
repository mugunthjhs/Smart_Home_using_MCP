import os
from pathlib import Path

class Config:
    BASE_DIR = Path(__file__).parent.parent
    DATABASE_PATH = BASE_DIR / "home_automation.db"

    API_HOST = os.getenv("API_HOST","0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # CORS settings
    CORS_ORIGINS = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative React dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # WebSocket settings
    WS_HEARTBEAT_INTERVAL = 30  # seconds
    
    # MCP settings
    MCP_SERVER_NAME = "home-automation-mcp"
    MCP_SERVER_VERSION = "1.0.0"
    
    # Update notification settings
    UPDATE_CHECK_INTERVAL = 0.1  # 100ms polling interval (checks database for MCP changes)


config = Config()