"""Seed data for home automation devices."""
import json
from datetime import datetime


SEED_DEVICES = [
    # Living Room
    {
        "id": "living_room_light_main",
        "type": "light",
        "room": "living_room",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 3000})
    },
    {
        "id": "living_room_light_accent",
        "type": "light",
        "room": "living_room",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 2700})
    },
    {
        "id": "living_room_temp",
        "type": "temperature_sensor",
        "room": "living_room",
        "state": "active",
        "properties": json.dumps({"value": 72, "unit": "F"})
    },
    {
        "id": "living_room_motion",
        "type": "motion_sensor",
        "room": "living_room",
        "state": "no_motion",
        "properties": json.dumps({"last_motion": None})
    },
    {
        "id": "living_room_blinds",
        "type": "blinds",
        "room": "living_room",
        "state": "open",
        "properties": json.dumps({"position": 100})
    },
    {
        "id": "fish_feeder",
        "type": "fish_feeder",
        "room": "living_room",
        "state": "idle",
        "properties": json.dumps({"last_fed": None})
    },
    
    # Bedroom
    {
        "id": "bedroom_light",
        "type": "light",
        "room": "bedroom",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 2700})
    },
    {
        "id": "bedroom_temp",
        "type": "temperature_sensor",
        "room": "bedroom",
        "state": "active",
        "properties": json.dumps({"value": 70, "unit": "F"})
    },
    {
        "id": "bedroom_motion",
        "type": "motion_sensor",
        "room": "bedroom",
        "state": "no_motion",
        "properties": json.dumps({"last_motion": None})
    },
    {
        "id": "bedroom_blinds",
        "type": "blinds",
        "room": "bedroom",
        "state": "closed",
        "properties": json.dumps({"position": 0})
    },
    {
        "id": "bedroom_fan",
        "type": "fan",
        "room": "bedroom",
        "state": "off",
        "properties": json.dumps({"speed": 0})
    },
    
    # Kitchen
    {
        "id": "kitchen_light_main",
        "type": "light",
        "room": "kitchen",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 4000})
    },
    {
        "id": "kitchen_light_under_cabinet",
        "type": "light",
        "room": "kitchen",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 3500})
    },
    {
        "id": "kitchen_temp",
        "type": "temperature_sensor",
        "room": "kitchen",
        "state": "active",
        "properties": json.dumps({"value": 73, "unit": "F"})
    },
    {
        "id": "kitchen_exhaust",
        "type": "fan",
        "room": "kitchen",
        "state": "off",
        "properties": json.dumps({"speed": 0})
    },
    
    # Bathroom
    {
        "id": "bathroom_light",
        "type": "light",
        "room": "bathroom",
        "state": "off",
        "properties": json.dumps({"brightness": 0, "color_temp": 4000})
    },
    {
        "id": "bathroom_exhaust",
        "type": "fan",
        "room": "bathroom",
        "state": "off",
        "properties": json.dumps({"speed": 0})
    },
    
    # Climate
    {
        "id": "thermostat_main",
        "type": "thermostat",
        "room": None,
        "state": "auto",
        "properties": json.dumps({
            "target_temp": 72,
            "current_temp": 71,
            "mode": "auto"
        })
    },
    
    # Security
    {
        "id": "front_door_lock",
        "type": "lock",
        "room": None,
        "state": "locked",
        "properties": json.dumps({})
    },
    {
        "id": "back_door_lock",
        "type": "lock",
        "room": None,
        "state": "locked",
        "properties": json.dumps({})
    },
    {
        "id": "garage_door",
        "type": "garage",
        "room": None,
        "state": "closed",
        "properties": json.dumps({})
    },
    
    # Outdoor
    {
        "id": "front_yard_sprinkler",
        "type": "sprinkler",
        "room": "outdoor",
        "state": "off",
        "properties": json.dumps({"zone": "front_yard", "duration": 15})
    },
    {
        "id": "back_yard_sprinkler",
        "type": "sprinkler",
        "room": "outdoor",
        "state": "off",
        "properties": json.dumps({"zone": "back_yard", "duration": 15})
    },
    {
        "id": "ev_charger",
        "type": "ev_charger",
        "room": "outdoor",
        "state": "idle",
        "properties": json.dumps({"battery_level": 85, "charging": False})
    },
]


async def seed_database(db):
    """Seed the database with initial devices if empty."""
    # Check if devices already exist
    async with db._connection.execute("SELECT COUNT(*) FROM devices") as cursor:
        count = (await cursor.fetchone())[0]
    
    if count > 0:
        print("Database already contains devices, skipping seed.")
        return
    
    print("Seeding database with initial devices...")
    
    # Insert all seed devices
    now = datetime.now().isoformat()
    for device in SEED_DEVICES:
        await db._connection.execute(
            """INSERT INTO devices (id, type, room, state, properties, last_updated)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                device["id"],
                device["type"],
                device["room"],
                device["state"],
                device["properties"],
                now
            )
        )
    
    await db._connection.commit()
    print(f"Successfully seeded {len(SEED_DEVICES)} devices.")
