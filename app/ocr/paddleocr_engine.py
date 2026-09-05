# app/ocr/paddleocr_engine.py
import logging
import numpy as np
from paddleocr import PaddleOCR
from app.ocr.base import OCREngine, OCRResult
from app.core.logging import logger

# Silence PaddleOCR debug logs
logging.getLogger("ppocr").setLevel(logging.ERROR)

class PaddleOCREngine(OCREngine):
    def __init__(self, conf_threshold: float):
        self.conf_threshold = conf_threshold
        logger.info("Initializing PaddleOCR (en) model...")
        self.ocr = PaddleOCR(use_angle_cls=False, lang='en')
        logger.info("PaddleOCR loaded successfully.")

    def recognize(self, image: np.ndarray) -> OCRResult:
        # Run OCR
        results = self.ocr.ocr(image, cls=False)
        
        if not results or not results[0]:
            return OCRResult(raw_text="", normalized_text="", confidence=0.0)

        # PaddleOCR returns a list of text blocks.
        # We assume a license plate is usually one main block, but we concatenate if there are multiple.
        raw_text_parts = []
        total_conf = 0.0
        valid_blocks = 0

        for block in results[0]:
            # block structure: [coords, (text, confidence)]
            text, conf = block[1]
            if conf >= self.conf_threshold:
                raw_text_parts.append(text)
                total_conf += conf
                valid_blocks += 1

        if valid_blocks == 0:
            return OCRResult(raw_text="", normalized_text="", confidence=0.0)

        raw_text = " ".join(raw_text_parts)
        avg_conf = total_conf / valid_blocks
        normalized_text = self.normalize_text(raw_text)

        return OCRResult(
            raw_text=raw_text,
            normalized_text=normalized_text,
            confidence=avg_conf
        )