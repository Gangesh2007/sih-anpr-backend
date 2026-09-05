# app/api/watchlist.py
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.alert_service import AlertService

router = APIRouter()
alert_service = AlertService()

class WatchlistItem(BaseModel):
    plate_number: str

@router.post("/")
def add_to_watchlist(item: WatchlistItem):
    plate = item.plate_number.upper().strip()
    alert_service.add_to_watchlist(plate)
    return {"status": "success", "message": f"{plate} added to watchlist"}

@router.get("/")
def get_watchlist():
    return {"watchlist": alert_service.get_watchlist()}

@router.delete("/{plate_number}")
def remove_from_watchlist(plate_number: str):
    plate = plate_number.upper().strip()
    alert_service.remove_from_watchlist(plate)
    return {"status": "success", "message": f"{plate} removed from watchlist"}