# app/api/search.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models.core_models import PlateObservation, Track, Camera

router = APIRouter()

@router.get("/plate/{plate_number}")
def search_vehicle_by_plate(plate_number: str, db: Session = Depends(get_db)):
    search_term = plate_number.upper().strip()
    
    # Join tables to get context about WHERE and WHEN the vehicle was seen
    results = (
        db.query(PlateObservation, Track, Camera)
        .join(Track, PlateObservation.track_id == Track.id)
        .join(Camera, Track.camera_id == Camera.id)
        .filter(PlateObservation.plate_number_normalized == search_term)
        .order_by(PlateObservation.timestamp.desc())
        .all()
    )
    
    response = []
    for obs, track, cam in results:
        response.append({
            "camera_id": cam.id,
            "location": cam.location_name,
            "timestamp": obs.timestamp,
            "plate_number": obs.plate_number_normalized,
            "confidence": obs.ocr_confidence,
            "vehicle_type": track.vehicle_type,
            "quality_score": obs.quality_score
        })
        
    return {"count": len(response), "results": response}