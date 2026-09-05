# app/preprocessing/frame.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Frame:
    camera_id: str
    frame_number: int
    timestamp: float
    image: np.ndarray  # The raw OpenCV image (BGR format)
    
    @property
    def height(self) -> int:
        return self.image.shape[0] if self.image is not None else 0
        
    @property
    def width(self) -> int:
        return self.image.shape[1] if self.image is not None else 0