# app/detection/roboflow_plate_detector.py
from typing import Optional
from inference_sdk import InferenceHTTPClient
from app.detection.plate_detector import PlateDetector, PlateDetection
from app.preprocessing.roi import VehicleROI
from app.core.config import settings
from app.core.logging import logger

class RoboflowPlateDetector(PlateDetector):
    def __init__(self, api_key: str, model_id: str, conf_threshold: float):
        if not api_key or api_key == "YOUR_ACTUAL_API_KEY_HERE":
            raise ValueError("Valid ROBOFLOW_API_KEY is required in .env")
        
        self.client = InferenceHTTPClient(
            api_url="https://detect.roboflow.com",
            api_key=api_key
        )
        self.model_id = model_id
        self.conf_threshold = conf_threshold
        logger.info(f"Initialized Roboflow Detector for model: {model_id}")

    def detect(self, roi: VehicleROI) -> Optional[PlateDetection]:
        # The inference API natively accepts OpenCV numpy arrays
        try:
            result = self.client.infer(roi.image, model_id=self.model_id)
        except Exception as e:
            logger.error(f"Roboflow API error: {e}")
            return None

        predictions = result.get("predictions", [])
        if not predictions:
            return None

        # Filter by confidence threshold
        valid_preds = [p for p in predictions if p["confidence"] >= self.conf_threshold]
        if not valid_preds:
            return None

        # Sort by confidence descending and pick the best candidate
        best_pred = sorted(valid_preds, key=lambda x: x["confidence"], reverse=True)[0]
        
        # Roboflow returns [center_x, center_y, width, height]
        cx, cy = best_pred["x"], best_pred["y"]
        w, h = best_pred["width"], best_pred["height"]
        
        # Convert to [x1, y1, x2, y2]
        x1, y1 = cx - (w / 2), cy - (h / 2)
        x2, y2 = cx + (w / 2), cy + (h / 2)

        return PlateDetection(
            bbox=[x1, y1, x2, y2],
            confidence=best_pred["confidence"],
            class_name=best_pred["class"]
        )