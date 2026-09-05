# app/preprocessing/quality.py
from dataclasses import dataclass

@dataclass
class PlateQuality:
    width: int
    height: int
    aspect_ratio: float
    sharpness: float
    brightness: float
    contrast: float
    quality_score: float
    is_usable: bool
    rejection_reason: str