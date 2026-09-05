# app/detection/plate_detector.py
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass
from app.preprocessing.roi import VehicleROI

@dataclass
class PlateDetection:
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_name: str

class PlateDetector(ABC):
    @abstractmethod
    def detect(self, roi: VehicleROI) -> Optional[PlateDetection]:
        """Runs inference on a vehicle ROI and returns the best plate bounding box."""
        pass