# app/ocr/paddleocr_engine.py
import logging
import numpy as np
import cv2
from app.schemas.observation import OCRResult
from paddleocr import PaddleOCR
from app.ocr.base import OCREngine, OCRResult
from app.core.logging import logger

# Silence PaddleOCR debug logs
logging.getLogger("ppocr").setLevel(logging.ERROR)

class PaddleOCREngine(OCREngine):
    def __init__(self, conf_threshold: float):
        self.conf_threshold = conf_threshold
        logger.info("Initializing PaddleOCR (en) model...")
        self.ocr = PaddleOCR(use_angle_cls=False, lang='en', enable_mkldnn=False)
        logger.info("PaddleOCR loaded successfully.")

    def recognize(self, image: np.ndarray) -> OCRResult:
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
        # Run OCR
        results = self.ocr.ocr(image)
        
        if not results or not results[0]:
            return OCRResult(raw_text="", normalized_text="", confidence=0.0)
            
        best_text = ""
        highest_conf = 0.0
        
        first_result = results[0]
        
        # --- NEW PADDLEX DICTIONARY PARSING ---
        if isinstance(first_result, dict) and 'rec_texts' in first_result:
            texts = first_result.get('rec_texts', [])
            scores = first_result.get('rec_scores', [])
            
            for i in range(len(texts)):
                text = str(texts[i]).strip()
                conf = float(scores[i]) if i < len(scores) else 0.5
                
                if conf > highest_conf:
                    highest_conf = conf
                    best_text = text
                    
        # --- FALLBACK FOR LEGACY TUPLE FORMAT ---
        elif isinstance(first_result, list):
            for block in first_result:
                if not block or len(block) < 2:
                    continue
                    
                prediction = block[1]
                if isinstance(prediction, (tuple, list)) and len(prediction) >= 2:
                    text = str(prediction[0]).strip()
                    conf = float(prediction[1])
                    
                    if conf > highest_conf:
                        highest_conf = conf
                        best_text = text

        # Clean the text (removes hyphens, spaces, and special chars)
        normalized = ''.join(e for e in best_text if e.isalnum()).upper()
                
        return OCRResult(
            raw_text=best_text, 
            normalized_text=normalized, 
            confidence=float(highest_conf)
        )