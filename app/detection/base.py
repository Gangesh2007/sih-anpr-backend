# app/detection/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from app.preprocessing.frame import Frame

@dataclass
class VehicleDetection:
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str

class VehicleDetector(ABC):
    @abstractmethod
    def detect(self, frame: Frame) -> List[VehicleDetection]:
        """Runs inference on a single frame and returns bounding boxes of target vehicles."""
        pass