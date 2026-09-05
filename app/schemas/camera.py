# app/schemas/camera.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CameraCreate(BaseModel):
    id: str
    name: str
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class CameraResponse(CameraCreate):
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True