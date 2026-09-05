# app/preprocessing/analyzer.py
import cv2
import numpy as np
from app.preprocessing.quality import PlateQuality
from app.preprocessing.roi import VehicleROI
from app.detection.plate_detector import PlateDetection

class PlateQualityAnalyzer:
    def __init__(self, min_width: int, min_height: int, blur_threshold: float, min_quality: float):
        self.min_width = min_width
        self.min_height = min_height
        self.blur_threshold = blur_threshold
        self.min_quality = min_quality
        
    def analyze(self, roi: VehicleROI, plate: PlateDetection) -> PlateQuality:
        # 1. Crop the exact plate image from the Vehicle ROI
        x1, y1, x2, y2 = map(int, plate.bbox)
        
        # Safely bound it within the image limits
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(roi.image.shape[1], x2), min(roi.image.shape[0], y2)
        
        plate_img = roi.image[y1:y2, x1:x2]
        width, height = x2 - x1, y2 - y1
        aspect_ratio = width / height if height > 0 else 0.0
        
        # Edge case: model returned a zero-area box
        if width == 0 or height == 0:
            return PlateQuality(0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, False, "EMPTY_CROP")
            
        # 2. Calculate CV Metrics
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        
        # Sharpness via Variance of Laplacian
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        
        # 3. Validation Logic
        is_usable = True
        rejection_reason = ""
        
        if width < self.min_width or height < self.min_height:
            is_usable = False
            rejection_reason = "TOO_SMALL"
        elif sharpness < self.blur_threshold:
            is_usable = False
            rejection_reason = "TOO_BLURRY"
            
        # Combine model confidence + sharpness into a normalized quality score
        quality_score = (plate.confidence * 0.5) + (min(sharpness / 500.0, 1.0) * 0.5)
        
        if quality_score < self.min_quality and is_usable:
            is_usable = False
            rejection_reason = "LOW_OVERALL_QUALITY"
            
        return PlateQuality(
            width=width, height=height, aspect_ratio=aspect_ratio,
            sharpness=sharpness, brightness=brightness, contrast=contrast,
            quality_score=quality_score, is_usable=is_usable,
            rejection_reason=rejection_reason
        )