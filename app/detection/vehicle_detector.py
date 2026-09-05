# app/detection/vehicle_detector.py
from typing import List
from ultralytics import YOLO
from app.detection.base import VehicleDetector, VehicleDetection
from app.preprocessing.frame import Frame
from app.core.logging import logger

class YOLOVehicleDetector(VehicleDetector):
    def __init__(self, model_path: str, conf_threshold: float):
        self.conf_threshold = conf_threshold
        
        logger.info(f"Loading YOLO model from: {model_path}")
        self.model = YOLO(model_path)
        
        # COCO dataset class mappings for vehicles
        self.target_classes = {
            2: 'car', 
            3: 'motorcycle', 
            5: 'bus', 
            7: 'truck'
        }
        logger.info(f"YOLO model loaded. Target classes: {list(self.target_classes.values())}")

    def detect(self, frame: Frame) -> List[VehicleDetection]:
        if frame.image is None:
            return []

        # Run inference restricted to target classes
        results = self.model.predict(
            source=frame.image,
            conf=self.conf_threshold,
            classes=list(self.target_classes.keys()),
            verbose=False
        )
        
        detections = []
        for result in results:
            if result.boxes is None:
                continue
                
            for box in result.boxes:
                # Convert tensor to standard Python types
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                
                if cls_id in self.target_classes:
                    detections.append(VehicleDetection(
                        bbox=[x1, y1, x2, y2],
                        confidence=conf,
                        class_id=cls_id,
                        class_name=self.target_classes[cls_id]
                    ))
                    
        return detections