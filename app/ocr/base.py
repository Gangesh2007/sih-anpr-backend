# app/ocr/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np
import re

@dataclass
class OCRResult:
    raw_text: str
    normalized_text: str
    confidence: float

class OCREngine(ABC):
    @abstractmethod
    def recognize(self, image: np.ndarray) -> OCRResult:
        """Performs OCR on a preprocessed image."""
        pass
        
    def normalize_text(self, text: str) -> str:
        """Removes spaces, special characters, and forces uppercase."""
        # Keep only alphanumeric characters
        clean = re.sub(r'[^A-Za-z0-9]', '', text)
        return clean.upper()