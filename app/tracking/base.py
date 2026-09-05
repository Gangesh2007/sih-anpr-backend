# app/tracking/base.py
from abc import ABC, abstractmethod
from typing import List
from app.preprocessing.frame import Frame
from app.detection.base import VehicleDetection
from app.schemas.track import TrackState

class Tracker(ABC):
    @abstractmethod
    def update(self, frame: Frame, detections: List[VehicleDetection]) -> List[TrackState]:
        """Takes a frame and its current detections, returns updated chronical track states."""
        pass