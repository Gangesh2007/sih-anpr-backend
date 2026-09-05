# app/services/alert_service.py
import asyncio
from app.websockets import manager
from app.core.logging import logger

# Global in-memory set to replace Redis
_MEMORY_WATCHLIST = set()

class AlertService:
    def __init__(self):
        # Always true since we are using local memory
        self.is_connected = True
            
    def check_and_alert(self, plate_number: str, camera_id: str, confidence: float):
        # O(1) lookup in local memory
        if plate_number in _MEMORY_WATCHLIST:
            logger.warning(f"🚨 ALERT! Watchlisted plate {plate_number} detected at {camera_id}!")
            
            alert_payload = {
                "type": "WATCHLIST_MATCH",
                "plate_number": plate_number,
                "camera_id": camera_id,
                "confidence": confidence,
                "message": f"Watchlisted vehicle {plate_number} spotted."
            }
            
            # Push to WebSockets asynchronously
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.broadcast_alert(alert_payload))
            except RuntimeError:
                asyncio.run(manager.broadcast_alert(alert_payload))
                
    def add_to_watchlist(self, plate_number: str):
        _MEMORY_WATCHLIST.add(plate_number.upper())

    def remove_from_watchlist(self, plate_number: str):
        _MEMORY_WATCHLIST.discard(plate_number.upper())

    def get_watchlist(self) -> list:
        return list(_MEMORY_WATCHLIST)