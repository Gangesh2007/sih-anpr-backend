# test_aggregation.py
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
from app.ocr.aggregator import OCRAggregator
from app.schemas.observation import PlateObservation
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
        min_width=int(os.getenv("PLATE_MIN_WIDTH", 15)),
        min_height=int(os.getenv("PLATE_MIN_HEIGHT", 5)),
        blur_threshold=float(os.getenv("BLUR_THRESHOLD", 50.0)),
        min_quality=float(os.getenv("MIN_PLATE_QUALITY", 0.4))
    )
    
    preprocessor = PlatePreprocessor()
    ocr_engine = PaddleOCREngine(conf_threshold=settings.OCR_CONF_THRESHOLD)
    
    print("\n--- Starting Full Aggregation Pipeline ---")
    
    frames_processed = 0
    for frame in source.get_frames():
        detections = vehicle_detector.detect(frame)
        tracks = tracker.update(frame, detections)
        
        for track in tracks:
            # 1. Collect Data while Active
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
                        if quality.is_usable:
                            px1, py1 = max(0, int(plate.bbox[0])), max(0, int(plate.bbox[1]))
                            px2, py2 = min(roi.image.shape[1], int(plate.bbox[2])), min(roi.image.shape[0], int(plate.bbox[3]))
                            raw_plate = roi.image[py1:py2, px1:px2]
                            enhanced = preprocessor.preprocess(raw_plate)
                            ocr = ocr_engine.recognize(enhanced)
                            
                            if ocr.normalized_text:
                                print(f"Frame {frame.frame_number} | Track {track.local_track_id} OCR: {ocr.normalized_text}")
                                obs = PlateObservation(
                                    frame_number=frame.frame_number, timestamp=frame.timestamp,
                                    raw_text=ocr.raw_text, normalized_text=ocr.normalized_text,
                                    ocr_confidence=ocr.confidence, plate_detection_confidence=plate.confidence,
                                    quality_score=quality.quality_score
                                )
                                track.plate_observations.append(obs)
            
            # 2. Aggregate when Track is Lost
            elif track.status == TrackStatus.LOST and len(track.plate_observations) > 0:
                final_result = OCRAggregator.aggregate(track.plate_observations)
                if final_result:
                    print(f"\n✅ FINAL DECISION FOR TRACK {track.local_track_id}: {final_result.plate_number}")
                    print(f"   Supported by {final_result.observation_count} frames, Avg Conf: {final_result.confidence:.2f}\n")
                    track.plate_observations.clear() # Clear so we don't print again
                    
        frames_processed += 1
        if frames_processed >= 30: # Run longer to let tracks leave the screen
            break
            
    source.release()

if __name__ == "__main__":
    test_pipeline()