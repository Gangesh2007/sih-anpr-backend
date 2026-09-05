# app/matching/cross_camera.py
from sqlalchemy.orm import Session
from app.database.models.core_models import Vehicle, VehicleObservation, Camera
from app.matching.spatial import haversine_distance
from app.core.logging import logger

class CrossCameraMatcher:
    def __init__(self, db: Session, max_speed_kmh: float = 160.0):
        self.db = db
        self.max_speed_kmh = max_speed_kmh
        
    def find_match(self, plate_number: str, timestamp: float, camera: Camera) -> Vehicle | None:
        """
        Attempts to find an existing global vehicle that physically could be 
        at this camera at this time.
        """
        # 1. Primary Signal: Exact plate match
        candidates = self.db.query(Vehicle).filter(Vehicle.plate_number == plate_number).all()
        
        if not candidates:
            return None
            
        for candidate in candidates:
            # 2. Temporal & Spatial verification
            last_obs = self.db.query(VehicleObservation).filter(
                VehicleObservation.vehicle_id == candidate.id
            ).order_by(VehicleObservation.timestamp.desc()).first()
            
            if not last_obs:
                return candidate # Should theoretically never happen, but safe fallback
                
            time_diff_hours = abs(timestamp - last_obs.timestamp) / 3600.0
            
            # If seen at the exact same time (or very close) on the same camera, it's valid
            if time_diff_hours < 0.01 and last_obs.camera_id == camera.id:
                return candidate
            
            # If we have geo-coordinates for both cameras, check physics
            if camera.latitude and camera.longitude and last_obs.latitude and last_obs.longitude:
                distance_km = haversine_distance(
                    camera.latitude, camera.longitude,
                    last_obs.latitude, last_obs.longitude
                )
                
                if time_diff_hours > 0:
                    required_speed = distance_km / time_diff_hours
                    if required_speed > self.max_speed_kmh:
                        logger.warning(f"Physics violation for plate {plate_number}! Required speed: {required_speed:.1f} km/h. Rejecting match.")
                        continue # Try next candidate (could be a cloned plate)
                        
            return candidate
            
        return None