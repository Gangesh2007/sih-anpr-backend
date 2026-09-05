# test_ocr.py
import os
from dotenv import load_dotenv
load_dotenv()

from app.preprocessing.video_source import OpenCVVideoSource
from app.detection.vehicle_detector import YOLOVehicleDetector
from app.tracking.bytetrack_tracker import ByteTrackTracker
from app.detection.roboflow_plate_detector import RoboflowPlateDetector
from app.preprocessing.analyzer import PlateQualityAnalyzer
from app.preprocessing.enhancement import PlatePreprocessor
from app.ocr.paddleocr_engine import PaddleOCREngine
from app.core.config import settings
from app.schemas.track import TrackStatus
from app.preprocessing.roi import VehicleROI

def test_pipeline():
    video_path = "data/videos/test_video.mp4"
    camera_id = "CAM_01"
    
    # Init all components
    source = OpenCVVideoSource(video_path, camera_id, settings.PROCESS_EVERY_N_FRAMES)
    vehicle_detector = YOLOVehicleDetector(settings.VEHICLE_MODEL_PATH, settings.VEHICLE_CONF_THRESHOLD)
    tracker = ByteTrackTracker(camera_id, track_max_age=settings.TRACK_MAX_AGE)
    plate_detector = RoboflowPlateDetector(os.getenv("ROBOFLOW_API_KEY"), os.getenv("ROBOFLOW_MODEL_ID"), settings.PLATE_CONF_THRESHOLD)
    
    analyzer = PlateQualityAnalyzer(
        min_width=int(os.getenv("PLATE_MIN_WIDTH", 60)),
        min_height=int(os.getenv("PLATE_MIN_HEIGHT", 20)),
        blur_threshold=float(os.getenv("BLUR_THRESHOLD", 100.0)),
        min_quality=float(os.getenv("MIN_PLATE_QUALITY", 0.4))
    )
    
    # NEW: Init Preprocessor & OCR
    preprocessor = PlatePreprocessor()
    ocr_engine = PaddleOCREngine(conf_threshold=settings.OCR_CONF_THRESHOLD)
    
    print("\n--- Starting Full CV Pipeline (Detection -> Quality -> Preproc -> OCR) ---")
    
    frames_processed = 0
    for frame in source.get_frames():
        detections = vehicle_detector.detect(frame)
        tracks = tracker.update(frame, detections)
        
        print(f"\nFrame {frame.frame_number} | Time: {frame.timestamp:.2f}s")
        
        for track in tracks:
            if track.status in [TrackStatus.NEW, TrackStatus.ACTIVE]:
                x1, y1, x2, y2 = map(int, track.last_bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.width, x2), min(frame.height, y2)
                
                if x2 > x1 and y2 > y1:
                    roi = VehicleROI(
                        camera_id=camera_id, track_id=track.local_track_id,
                        frame_number=frame.frame_number, timestamp=frame.timestamp,
                        bbox=[x1, y1, x2, y2], image=frame.image[y1:y2, x1:x2]
                    )
                    
                    plate = plate_detector.detect(roi)
                    if plate:
                        quality = analyzer.analyze(roi, plate)
                        
                        # We only run OCR on usable plates!
                        if quality.is_usable:
                            # 1. Crop plate
                            px1, py1, px2, py2 = map(int, plate.bbox)
                            px1, py1 = max(0, px1), max(0, py1)
                            px2, py2 = min(roi.image.shape[1], px2), min(roi.image.shape[0], py2)
                            raw_plate_img = roi.image[py1:py2, px1:px2]
                            
                            # 2. Preprocess
                            enhanced_img = preprocessor.preprocess(raw_plate_img)
                            
                            # 3. OCR
                            ocr_result = ocr_engine.recognize(enhanced_img)
                            
                            if ocr_result.normalized_text:
                                print(f"  -> Track {track.local_track_id} OCR: [{ocr_result.normalized_text}] (Conf: {ocr_result.confidence:.2f})")
                            else:
                                print(f"  -> Track {track.local_track_id} OCR: [No Text Found]")
                        else:
                            print(f"  -> Track {track.local_track_id}: Plate Ignored ({quality.rejection_reason})")
                            
        frames_processed += 1
        if frames_processed >= 10: 
            break
            
    source.release()

if __name__ == "__main__":
    test_pipeline()