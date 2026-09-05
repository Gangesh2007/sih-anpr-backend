# app/matching/global_identity.py
from sqlalchemy.orm import Session
from app.database.models.core_models import Vehicle, VehicleObservation, Track, Camera
from app.matching.cross_camera import CrossCameraMatcher
from app.core.logging import logger

class GlobalIdentityResolver:
    @staticmethod
    def resolve_and_store(db: Session, track: Track, plate_text: str, plate_conf: float):
        camera = db.query(Camera).filter(Camera.id == track.camera_id).first()
        if not camera:
            return None

        matcher = CrossCameraMatcher(db)
        matched_vehicle = matcher.find_match(plate_text, track.last_seen, camera)
        
        if matched_vehicle:
            # Update existing vehicle
            matched_vehicle.last_seen = track.last_seen
            if plate_conf > matched_vehicle.plate_confidence:
                matched_vehicle.plate_confidence = plate_conf
                
            logger.info(f"Cross-Camera Match: Track {track.local_track_id} -> Global {matched_vehicle.id}")
        else:
            # Mint a new global vehicle
            matched_vehicle = Vehicle(
                plate_number=plate_text,
                plate_confidence=plate_conf,
                vehicle_type=track.vehicle_type,
                vehicle_color=track.vehicle_color,
                first_seen=track.first_seen,
                last_seen=track.last_seen
            )
            db.add(matched_vehicle)
            db.flush()
            logger.info(f"Minted new Global Vehicle {matched_vehicle.id} for Track {track.local_track_id}")

        # Create the Observation link
        observation = VehicleObservation(
            vehicle_id=matched_vehicle.id,
            camera_id=camera.id,
            track_id=track.id,
            timestamp=track.last_seen,
            confidence=plate_conf,
            latitude=camera.latitude,
            longitude=camera.longitude
        )
        db.add(observation)
        db.commit()
        
        return matched_vehicle