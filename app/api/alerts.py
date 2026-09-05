# app/api/alerts.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websockets import manager
from app.core.logging import logger

router = APIRouter()

@router.websocket("/ws")
async def alert_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive and wait for incoming pings/messages from the client
            data = await websocket.receive_text()
            # If the frontend sends a ping, we could respond here.
            # For now, we just keep the loop running so it can receive server broadcasts.
    except WebSocketDisconnect:
        manager.disconnect(websocket)