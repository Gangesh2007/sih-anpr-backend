# app/preprocessing/roi.py
from dataclasses import dataclass
import numpy as np

@dataclass
class VehicleROI:
    camera_id: str
    track_id: int
    frame_number: int
    timestamp: float
    bbox: list[float]
    image: np.ndarray