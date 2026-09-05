# app/schemas/track.py
from enum import Enum
from typing import List
from pydantic import BaseModel

class TrackStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    LOST = "LOST"
    FINISHED = "FINISHED"

class TrackState(BaseModel):
    camera_id: str
    local_track_id: int
    first_seen: float
    last_seen: float
    last_bbox: List[float]
    vehicle_type: str
    vehicle_color: str = "unknown"
    plate_observations: List[dict] = []
    status: TrackStatus = TrackStatus.NEW