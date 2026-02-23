"""FastMCP Server for Home Automation - stdio protocol for AI assistants."""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Literal
from datetime import datetime
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP
import logging

logger = logging.getLogger("mcp_tools")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import config
from app.db.database import db
from app.utils.websocket_manager import ws_manager


# Lifespan context manager for database
@asynccontextmanager
async def lifespan_context(app):
    """Initialize database connection."""
    await db.connect()
    await db.initialize_schema()
    print("MCP Server: Database connected")
    yield
    await db.disconnect()
    print("MCP Server: Database disconnected")


# Create FastMCP server
mcp = FastMCP(
    name=config.MCP_SERVER_NAME,
    lifespan=lifespan_context,
    instructions="""
    You are a smart home automation assistant. You can control lights, thermostats, locks,
    blinds, fans, garage doors, sprinklers, EV chargers, and other smart home devices.
    
    You can also set home modes (home, away, sleep, vacation) which trigger multiple
    device actions at once.
    
    Always confirm actions taken and provide clear feedback about device states.
    """
)


# Helper function to signal updates to WebSocket clients
def signal_ws_update(update_type: str, **kwargs):
    """Signal WebSocket manager about updates."""
    update_data = {"type": update_type, **kwargs}
    ws_manager.signal_update(update_data)



@mcp.tool()
async def control_device(
    action: Literal["on", "off", "open", "close", "set", "toggle", "lock", "unlock"],
    device_id: Optional[str] = None,
    room: Optional[str] = None,
    device_type: Optional[str] = None,
    brightness: Optional[int] = None,
    position: Optional[int] = None,
    speed: Optional[int] = None,
    target_temp: Optional[int] = None,
    mode: Optional[str] = None
) -> str:

    """
    Universal device control tool. Control smart home devices by ID, room, or type.
    
    Args:
        action: Action to perform (on, off, open, close, set, toggle, lock, unlock)
        device_id: Specific device ID (optional)
        room: Control all devices of a type in a room (optional)
        device_type: Type of device to control (optional)
        brightness: Light brightness 0-100 (optional)
        position: Blinds position 0-100 (optional)
        speed: Fan speed 0-3 (optional)
        target_temp: Thermostat target temperature (optional)
        mode: Thermostat mode: heat, cool, auto, off (optional)
    
    Examples:
        - Turn on living room lights: control_device("on", room="livingroom", device_type="light")
        - Set bedroom temp: control_device("set", device_id="thermostat_main", target_temp=72)
        - Close all blinds: control_device("close", device_type="blinds")
    """
        
    if room:
        room = room.replace(" ", "_").lower()

    if device_type:
        device_type = device_type.lower()

    # Get target devices
    if device_id:
        devices = [await db.get_device(device_id)]
        if not devices[0]:
            return f"❌ Device '{device_id}' not found."
    else:
        devices = await db.get_devices(room=room, device_type=device_type)
    
    if not devices:
        filter_desc = []
        if room:
            filter_desc.append(f"room={room}")
        if device_type:
            filter_desc.append(f"type={device_type}")
        return f"❌ No devices found matching: {', '.join(filter_desc)}"
    
    results = []
    
    for device in devices:
        dev_id = device["id"]
        dev_type = device["type"]
        current_state = device["state"]
        properties = device.get("properties", {})
        
        # Determine new state and properties based on action and device type
        new_state = None
        new_properties = properties.copy()
        
        # Handle actions
        if action in ["on", "off"]:
            if dev_type in ["light", "fan", "sprinkler", "ev_charger"]:
                new_state = action
                if dev_type == "light" and brightness is not None:
                    new_properties["brightness"] = max(0, min(100, brightness))
                elif dev_type == "light" and action == "on" and new_properties.get("brightness", 0) == 0:
                    new_properties["brightness"] = 100
                elif dev_type == "light" and action == "off":
                    new_properties["brightness"] = 0
                elif dev_type == "fan" and speed is not None:
                    new_properties["speed"] = max(0, min(3, speed))
        
        elif action in ["open", "close"]:
            if dev_type in ["blinds", "garage"]:
                new_state = action
                if dev_type == "blinds":
                    new_properties["position"] = 100 if action == "open" else 0
                    if position is not None:
                        new_properties["position"] = max(0, min(100, position))
                        new_state = "open" if position > 0 else "closed"
        
        elif action in ["lock", "unlock"]:
            if dev_type == "lock":
                new_state = "locked" if action == "lock" else "unlocked"
        
        elif action == "set":
            if dev_type == "light" and brightness is not None:
                new_state = "on" if brightness > 0 else "off"
                new_properties["brightness"] = max(0, min(100, brightness))
            elif dev_type == "blinds" and position is not None:
                new_properties["position"] = max(0, min(100, position))
                new_state = "open" if position > 0 else "closed"
            elif dev_type == "fan" and speed is not None:
                new_properties["speed"] = max(0, min(3, speed))
                new_state = "on" if speed > 0 else "off"
            elif dev_type == "thermostat":
                if target_temp is not None:
                    new_properties["target_temp"] = target_temp
                if mode is not None:
                    new_properties["mode"] = mode
                    new_state = mode
        
        elif action == "toggle":
            if dev_type in ["light", "fan"]:
                new_state = "off" if current_state == "on" else "on"
                if dev_type == "light":
                    new_properties["brightness"] = 100 if new_state == "on" else 0
            elif dev_type in ["blinds", "garage"]:
                new_state = "closed" if current_state == "open" else "open"
                if dev_type == "blinds":
                    new_properties["position"] = 0 if new_state == "closed" else 100
            elif dev_type == "lock":
                new_state = "unlocked" if current_state == "locked" else "locked"
        
        # Update device if state changed
        if new_state or new_properties != properties:
            await db.update_device(dev_id, state=new_state, properties=new_properties)
            await db.log_event("device_control", dev_id, action, {"new_state": new_state, "properties": new_properties})
            
            # Signal WebSocket update
            signal_ws_update(
                "device_update",
                device_id=dev_id,
                room=device.get("room"),
                device_type=dev_type,
                state=new_state or current_state,
                properties=new_properties
            )
            
            result_msg = f"✅ {dev_id}: {current_state} → {new_state or current_state}"
            if dev_type == "light" and "brightness" in new_properties:
                result_msg += f" (brightness: {new_properties['brightness']}%)"
            elif dev_type == "thermostat" and "target_temp" in new_properties:
                result_msg += f" (target: {new_properties['target_temp']}°F)"
            results.append(result_msg)
        else:
            results.append(f"ℹ️ {dev_id}: No change needed (already {current_state})")
    
    return "\n".join(results)

@mcp.tool()
async def open_garage() -> str:
    """Open the garage door."""
    
    garage = await db.get_devices(device_type="garage")

    if not garage:
        return "❌ Garage door not found."

    device = garage[0]

    await db.update_device(device["id"], state="open")

    signal_ws_update(
        "device_update",
        device_id=device["id"],
        state="open"
    )

    return "🚗 Garage door opened."


@mcp.tool()
async def get_device_status(
    device_id: Optional[str] = None,
    room: Optional[str] = None,
    device_type: Optional[str] = None
) -> str:
    """
    Query device states and information.
    
    Args:
        device_id: Specific device ID (optional)
        room: Filter by room (optional)
        device_type: Filter by device type (optional)
    
    Examples:
        - All devices: get_device_status()
        - Bedroom devices: get_device_status(room="bedroom")
        - All locks: get_device_status(device_type="lock")
    """
    logger.info("Tool called: get_device_status")

    if device_id:
        device = await db.get_device(device_id)
        if not device:
            return f"Device '{device_id}' not found."
        devices = [device]
    else:
        devices = await db.get_devices(room=room, device_type=device_type)

    if not devices:
        return "No devices found."

    # Group by room
    by_room = {}
    no_room = []

    for device in devices:
        if device.get("room"):
            room_name = device["room"]
            if room_name not in by_room:
                by_room[room_name] = []
            by_room[room_name].append(device)
        else:
            no_room.append(device)

    output = []

    for room_name in sorted(by_room.keys()):
        room_devices = by_room[room_name]
        output.append(f"\n[{room_name.replace('_', ' ').title()}]")
        for device in room_devices:
            output.append(format_device_status(device))

    if no_room:
        output.append("\n[SYSTEM]")
        for device in no_room:
            output.append(format_device_status(device))

    output = "\n".join(output)
    logger.debug(output)

    return output


def format_device_status(device: dict) -> str:
    """Format a device status for display."""

    icons = {
        "light": "[LIGHT]",
        "fan": "[FAN]",
        "blinds": "[BLINDS]",
        "thermostat": "[THERMOSTAT]",
        "lock": "[LOCK]",
        "garage": "[GARAGE]",
        "temperature_sensor": "[TEMP_SENSOR]",
        "motion_sensor": "[MOTION]",
        "sprinkler": "[SPRINKLER]",
        "ev_charger": "[EV]",
        "fish_feeder": "[FEEDER]"
    }

    icon = icons.get(device["type"], "[DEVICE]")
    name = device["id"].replace("_", " ").title()
    state = device["state"].upper()
    props = device.get("properties", {})

    details = []

    if device["type"] == "light" and "brightness" in props:
        details.append(f"{props['brightness']}%")

    elif device["type"] == "temperature_sensor" and "value" in props:
        details.append(f"{props['value']} {props.get('unit', 'F')}")

    elif device["type"] == "thermostat":
        details.append(
            f"Target: {props.get('target_temp')} F, Current: {props.get('current_temp')} F"
        )

    elif device["type"] == "blinds" and "position" in props:
        details.append(f"{props['position']}%")

    elif device["type"] == "ev_charger" and "battery_level" in props:
        details.append(f"Battery: {props['battery_level']}%")

    detail_str = f" [{', '.join(details)}]" if details else ""

    return f"  {icon} {name}: {state}{detail_str}"


@mcp.tool()
async def get_sensor_reading(
    sensor_type: Literal["temperature", "motion", "humidity", "air_quality"],
    room: Optional[str] = None
) -> str:
    """
    Read sensor data from temperature, motion, and other sensors.
    
    Args:
        sensor_type: Type of sensor to read
        room: Specific room (optional)
    
    Examples:
        - Living room temp: get_sensor_reading("temperature", room="living_room")
        - All temperatures: get_sensor_reading("temperature")
    """
    
    # Map sensor types to device types
    type_map = {
        "temperature": "temperature_sensor",
        "motion": "motion_sensor"
    }
    
    device_type = type_map.get(sensor_type)
    if not device_type:
        return f"❌ Sensor type '{sensor_type}' not supported. Use: temperature, motion"
    
    devices = await db.get_devices(room=room, device_type=device_type)
    
    if not devices:
        location = f" in {room}" if room else ""
        return f"No {sensor_type} sensors found{location}."
    
    output = [f"🌡️ {sensor_type.title()} Sensors:\n"]
    
    for device in devices:
        room_name = device.get("room", "System").replace("_", " ").title()
        props = device.get("properties", {})
        
        if sensor_type == "temperature":
            value = props.get("value", "N/A")
            unit = props.get("unit", "F")
            output.append(f"  📍 {room_name}: {value}°{unit}")
        elif sensor_type == "motion":
            state = "🔴 Motion detected" if device["state"] == "motion" else "🟢 No motion"
            last_motion = props.get("last_motion")
            if last_motion:
                output.append(f"  📍 {room_name}: {state} (last: {last_motion})")
            else:
                output.append(f"  📍 {room_name}: {state}")
    
    return "\n".join(output)


@mcp.tool()
async def set_home_mode(
    mode: Literal["home", "away", "sleep", "vacation"]
) -> str:
    """
    Set home automation mode, which triggers multiple device actions.
    
    Modes:
        - home: Welcome mode (lights on, comfortable temp 72°F)
        - away: Security mode (lights off, locks engaged, temp 65°F)
        - sleep: Night mode (most lights off, bedroom dim, doors locked, temp 68°F)
        - vacation: Extended away (all lights off, all secured, temp 60°F)
    
    Args:
        mode: Mode to activate
    
    Example:
        - Going to bed: set_home_mode("sleep")
    """
    
    # Get all devices
    devices = await db.get_devices()
    
    actions = []
    
    # Define mode behaviors
    if mode == "home":
        # Turn on main lights, set comfortable temp
        for device in devices:
            if device["type"] == "light" and "main" in device["id"]:
                await db.update_device(device["id"], state="on", properties={"brightness": 75, **device.get("properties", {})})
                actions.append(f"💡 {device['id']}: ON (75%)")
            elif device["type"] == "thermostat":
                props = device.get("properties", {})
                props["target_temp"] = 72
                props["mode"] = "auto"
                await db.update_device(device["id"], state="auto", properties=props)
                actions.append(f"🌡️ Thermostat: 72°F (auto)")
    
    elif mode == "away":
        # Turn off lights, lock doors, lower temp
        for device in devices:
            if device["type"] == "light":
                await db.update_device(device["id"], state="off", properties={"brightness": 0, **device.get("properties", {})})
                actions.append(f"💡 {device['id']}: OFF")
            elif device["type"] == "lock" and device["state"] != "locked":
                await db.update_device(device["id"], state="locked")
                actions.append(f"🔒 {device['id']}: LOCKED")
            elif device["type"] == "thermostat":
                props = device.get("properties", {})
                props["target_temp"] = 65
                await db.update_device(device["id"], properties=props)
                actions.append(f"🌡️ Thermostat: 65°F")
    
    elif mode == "sleep":
        # Most lights off, bedroom dim, lock doors
        for device in devices:
            if device["type"] == "light":
                if "bedroom" in device["id"]:
                    await db.update_device(device["id"], state="on", properties={"brightness": 20, **device.get("properties", {})})
                    actions.append(f"💡 {device['id']}: DIM (20%)")
                else:
                    await db.update_device(device["id"], state="off", properties={"brightness": 0, **device.get("properties", {})})
                    actions.append(f"💡 {device['id']}: OFF")
            elif device["type"] == "lock" and device["state"] != "locked":
                await db.update_device(device["id"], state="locked")
                actions.append(f"🔒 {device['id']}: LOCKED")
            elif device["type"] == "thermostat":
                props = device.get("properties", {})
                props["target_temp"] = 68
                await db.update_device(device["id"], properties=props)
                actions.append(f"🌡️ Thermostat: 68°F")
    
    elif mode == "vacation":
        # Everything off and secured
        for device in devices:
            if device["type"] == "light":
                await db.update_device(device["id"], state="off", properties={"brightness": 0, **device.get("properties", {})})
                actions.append(f"💡 {device['id']}: OFF")
            elif device["type"] == "lock" and device["state"] != "locked":
                await db.update_device(device["id"], state="locked")
                actions.append(f"🔒 {device['id']}: LOCKED")
            elif device["type"] == "garage" and device["state"] != "closed":
                await db.update_device(device["id"], state="closed")
                actions.append(f"🚗 Garage: CLOSED")
            elif device["type"] == "thermostat":
                props = device.get("properties", {})
                props["target_temp"] = 60
                await db.update_device(device["id"], properties=props)
                actions.append(f"🌡️ Thermostat: 60°F")
    
    # Update mode in database
    await db.set_home_mode(mode)
    await db.log_event("mode_change", action=mode, metadata={"actions_count": len(actions)})
    
    # Signal WebSocket update
    signal_ws_update("mode_change", mode=mode)
    
    return f"🏠 Home mode set to: {mode.upper()}\n\nActions taken:\n" + "\n".join(actions)


@mcp.tool()
async def get_home_mode() -> str:
    """
    Get the current home automation mode.
    
    Returns the currently active mode (home, away, sleep, vacation).
    """
    
    mode = await db.get_active_mode()
    
    if not mode:
        return "❓ No active mode set."
    
    mode_descriptions = {
        "home": "🏠 Welcome mode - lights on, comfortable temperature",
        "away": "🚪 Security mode - lights off, doors locked, energy saving",
        "sleep": "🌙 Night mode - bedroom dimmed, doors locked, quiet",
        "vacation": "✈️ Extended away - everything secured and minimal energy"
    }
    
    description = mode_descriptions.get(mode, "")
    return f"Current mode: {mode.upper()}\n{description}"


@mcp.tool()
async def feed_fish() -> str:
    """
    Trigger the automatic fish feeder.
    
    Activates the fish feeder and logs the feeding time.
    """
    
    feeder = await db.get_device("fish_feeder")
    
    if not feeder:
        return "❌ Fish feeder not found."
    
    # Update feeder state
    now = datetime.now().isoformat()
    props = feeder.get("properties", {})
    props["last_fed"] = now
    
    await db.update_device("fish_feeder", state="feeding", properties=props)
    await db.log_event("fish_feeding", "fish_feeder", "feed", {"timestamp": now})
    
    # Signal update
    signal_ws_update("device_update", device_id="fish_feeder", state="feeding", properties=props)
    
    # Reset to idle after a moment (simulated)
    await asyncio.sleep(0.5)
    await db.update_device("fish_feeder", state="idle", properties=props)
    signal_ws_update("device_update", device_id="fish_feeder", state="idle", properties=props)
    
    return f"🐠 Fish fed successfully at {datetime.now().strftime('%I:%M %p')}"


@mcp.tool()
async def water_plants(
    zone: Optional[Literal["front_yard", "back_yard"]] = None,
    duration: int = 15
) -> str:
    """
    Activate the sprinkler system to water plants.
    
    Args:
        zone: Which zone to water (front_yard, back_yard, or both if not specified)
        duration: Duration in minutes (default: 15)
    
    Examples:
        - Water front yard: water_plants(zone="front_yard", duration=10)
        - Water all zones: water_plants(duration=20)
    """
    
    # Get sprinklers
    sprinklers = await db.get_devices(device_type="sprinkler")
    
    if not sprinklers:
        return "❌ No sprinkler systems found."
    
    # Filter by zone if specified
    if zone:
        sprinklers = [s for s in sprinklers if s.get("properties", {}).get("zone") == zone]
    
    if not sprinklers:
        return f"❌ No sprinklers found for zone: {zone}"
    
    actions = []
    
    for sprinkler in sprinklers:
        props = sprinkler.get("properties", {})
        props["duration"] = duration
        zone_name = props.get("zone", "unknown")
        
        await db.update_device(sprinkler["id"], state="on", properties=props)
        await db.log_event("watering", sprinkler["id"], "start", {"duration": duration, "zone": zone_name})
        
        signal_ws_update("device_update", device_id=sprinkler["id"], state="on", properties=props)
        
        actions.append(f"💧 {zone_name.replace('_', ' ').title()}: ON for {duration} minutes")
    
    return "🌱 Watering started:\n" + "\n".join(actions)


@mcp.tool()
async def start_ev_charging() -> str:
    """
    Start charging the electric vehicle.
    
    Activates the EV charger to begin charging the connected vehicle.
    """
    
    charger = await db.get_device("ev_charger")
    
    if not charger:
        return "❌ EV charger not found."
    
    if charger["state"] == "charging":
        return "ℹ️ EV is already charging."
    
    props = charger.get("properties", {})
    props["charging"] = True
    
    await db.update_device("ev_charger", state="charging", properties=props)
    await db.log_event("ev_charging", "ev_charger", "start")
    
    signal_ws_update("device_update", device_id="ev_charger", state="charging", properties=props)
    
    battery = props.get("battery_level", 0)
    return f"🔌 EV charging started. Current battery: {battery}%"


@mcp.tool()
async def stop_ev_charging() -> str:
    """
    Stop charging the electric vehicle.
    
    Deactivates the EV charger and stops the charging process.
    """
    
    charger = await db.get_device("ev_charger")
    
    if not charger:
        return "❌ EV charger not found."
    
    if charger["state"] != "charging":
        return "ℹ️ EV is not currently charging."
    
    props = charger.get("properties", {})
    props["charging"] = False
    
    await db.update_device("ev_charger", state="idle", properties=props)
    await db.log_event("ev_charging", "ev_charger", "stop")
    
    signal_ws_update("device_update", device_id="ev_charger", state="idle", properties=props)
    
    battery = props.get("battery_level", 0)
    return f"🔌 EV charging stopped. Battery level: {battery}%"


if __name__ == "__main__":
    # Run the MCP server with stdio transport
    mcp.run(transport="stdio")
