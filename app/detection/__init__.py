from dataclasses import dataclass

@dataclass
class VehicleDetection:
    bbox: list[float]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str