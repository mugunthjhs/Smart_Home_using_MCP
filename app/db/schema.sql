-- Home Automation Database Schema

--Devices table: store all devices of home
CREATE TABLE IF NOT EXISTS devices(
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    room TEXT,
    state TEXT NOT NULL,
    properties TEXT,  -- JSON string
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


--Events table: logging all events 
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    device_id TEXT, 
    action TEXT,
    metadata TEXT,  -- JSON string
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Home modes table: tracks home automation modes
CREATE TABLE IF NOT EXISTS home_modes (
    mode TEXT PRIMARY KEY,
    is_active BOOLEAN DEFAULT 0,
    last_activated TIMESTAMP
);

-- Automations table: stores automation rules (optional/future)
CREATE TABLE IF NOT EXISTS automations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    trigger TEXT NOT NULL,  -- JSON string
    actions TEXT NOT NULL,  -- JSON string
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize home modes
INSERT OR IGNORE INTO home_modes (mode, is_active) VALUES 
    ('home', 1),
    ('away', 0),
    ('sleep', 0),
    ('vacation', 0);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_devices_room ON devices(room);
CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(type);
CREATE INDEX IF NOT EXISTS idx_devices_state ON devices(state);
CREATE INDEX IF NOT EXISTS idx_events_device_id ON events(device_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
