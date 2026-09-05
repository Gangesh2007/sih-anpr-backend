# app/websockets.py
from fastapi import WebSocket
from typing import List
import json
from app.core.logging import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard connected. Active clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Dashboard disconnected.")

    async def broadcast_alert(self, alert_data: dict):
        if not self.active_connections:
            return
            
        message = json.dumps(alert_data)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")

manager = ConnectionManager()