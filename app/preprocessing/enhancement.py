# app/preprocessing/enhancement.py
import cv2
import numpy as np

class PlatePreprocessor:
    @staticmethod
    def preprocess(image: np.ndarray) -> np.ndarray:
        """Enhances a cropped license plate for OCR."""
        # 1. Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. Resize to a height of ~64px (optimal for most CRNN OCR models)
        # Maintain aspect ratio
        h, w = gray.shape
        target_h = 64
        scale = target_h / h
        target_w = int(w * scale)
        resized = cv2.resize(gray, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
        
        # 3. Contrast Limited Adaptive Histogram Equalization (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(resized)
        
        # 4. Slight Gaussian Blur to remove high-frequency noise from resizing
        smoothed = cv2.GaussianBlur(enhanced, (3, 3), 0)
        
        return smoothed