# 🏠 Home Automation API & MCP Server

A robust, asynchronous home automation backend powered by **FastAPI** and **FastMCP**. This system manages smart devices (lights, thermostats, locks, etc.) via a SQLite database and provides real-time updates through WebSockets and an AI-ready Model Context Protocol (MCP) server.

## 🚀 Features

* **Asynchronous Core**: Built with `FastAPI` and `aiosqlite` for high-performance, non-blocking I/O.
* **Real-time Synchronization**: Background database polling and WebSocket management to keep all clients in sync.
* **AI-Ready (MCP)**: Includes a FastMCP server, allowing AI assistants (like Claude or Gemini) to control your home using natural language.
* **Flexible Schema**: Supports various device types including lights, fans, blinds, locks, and sensors with JSON-based property storage.
* **Auto-Initialization**: Automatically creates database schemas and seeds initial data on startup.

---

## 🛠️ Project Structure

* `app/main.py`: The FastAPI application entry point.
* `app/mcp_server.py`: The FastMCP server for AI assistant integration.
* `app/db/database.py`: Core database logic and SQLite connection handling.
* `app/db/seed_data.py`: Initial default devices and state configurations.
* `app/models/`: Pydantic models for data validation and API schemas.
* `app/config.py`: Centralized configuration management.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/devices` | List all devices (filterable by room/type). |
| `GET` | `/api/rooms` | Get a list of all unique rooms. |
| `GET` | `/api/stats` | Get dashboard statistics (lights on, locked doors). |
| `WS` | `/ws` | WebSocket endpoint for real-time state updates. |

---

## 🤖 MCP Tools for AI

The system exposes the `control_device` tool to AI assistants, enabling actions like:
- *"Turn on the living room lights."*
- *"Set the bedroom temperature to 72°F."*
- *"Lock all the doors."*
- *"Close the blinds to 50%."*

---

## ⚙️ Installation & Setup

### 1. Requirements
- Python 3.10+
- `pip install fastapi uvicorn aiosqlite pydantic mcp`

### 2. Configuration
Environment variables can be set or modified in `app/config.py`:
- `API_PORT`: Default is `8000`.
- `DATABASE_PATH`: Default is `home_automation.db`.

### 3. Running the API
```bash
python -m app.main
