# app/schemas/observation.py
from pydantic import BaseModel
from typing import List

class PlateObservation(BaseModel):
    frame_number: int
    timestamp: float
    raw_text: str
    normalized_text: str
    ocr_confidence: float
    plate_detection_confidence: float
    quality_score: float

class AggregatedPlateResult(BaseModel):
    plate_number: str
    confidence: float
    observation_count: int
    supporting_frames: List[int]