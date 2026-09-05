# app/api/trajectories.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models.core_models import Vehicle, VehicleObservation, Camera
from app.schemas.trajectory import TrajectoryResponse, TrajectoryPoint
from app.matching.spatial import haversine_distance

router = APIRouter()

@router.get("/{vehicle_id}", response_model=TrajectoryResponse)
def get_vehicle_trajectory(vehicle_id: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Global Vehicle not found")

    # Fetch all observations for this vehicle, strictly ordered by time
    observations = (
        db.query(VehicleObservation, Camera)
        .join(Camera, VehicleObservation.camera_id == Camera.id)
        .filter(VehicleObservation.vehicle_id == vehicle_id)
        .order_by(VehicleObservation.timestamp.asc())
        .all()
    )

    path = []
    total_distance = 0.0

    for i, (obs, cam) in enumerate(observations):
        point = TrajectoryPoint(
            camera_id=cam.id,
            location_name=cam.location_name,
            latitude=cam.latitude,
            longitude=cam.longitude,
            timestamp=obs.timestamp,
            confidence=obs.confidence,
            sequence_number=i + 1
        )
        path.append(point)

        # Calculate distance from the previous camera location
        if i > 0:
            prev_cam = observations[i-1][1]
            if cam.latitude and cam.longitude and prev_cam.latitude and prev_cam.longitude:
                dist = haversine_distance(
                    prev_cam.latitude, prev_cam.longitude,
                    cam.latitude, cam.longitude
                )
                total_distance += dist

    # Calculate time difference between first and last sighting
    duration = path[-1].timestamp - path[0].timestamp if path else 0.0

    return TrajectoryResponse(
        vehicle_id=vehicle.id,
        plate_number=vehicle.plate_number,
        first_seen=vehicle.first_seen,
        last_seen=vehicle.last_seen,
        total_duration_seconds=duration,
        total_distance_km=total_distance,
        path=path
    )