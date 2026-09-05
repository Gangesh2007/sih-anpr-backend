# app/schemas/trajectory.py
from pydantic import BaseModel
from typing import List, Optional

class TrajectoryPoint(BaseModel):
    camera_id: str
    location_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: float
    confidence: float
    sequence_number: int

class TrajectoryResponse(BaseModel):
    vehicle_id: str
    plate_number: str
    first_seen: float
    last_seen: float
    total_duration_seconds: float
    total_distance_km: float
    path: List[TrajectoryPoint]