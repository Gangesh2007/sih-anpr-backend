# test_quality.py
import os
from dotenv import load_dotenv
load_dotenv() # Force load to get the newly added env vars

from app.preprocessing.video_source import OpenCVVideoSource
from app.detection.vehicle_detector import YOLOVehicleDetector
from app.tracking.bytetrack_tracker import ByteTrackTracker
from app.detection.roboflow_plate_detector import RoboflowPlateDetector
from app.preprocessing.analyzer import PlateQualityAnalyzer
from app.core.config import settings
from app.schemas.track import TrackStatus
from app.preprocessing.roi import VehicleROI

def test_pipeline():
    video_path = "data/videos/test_video.mp4"
    camera_id = "CAM_01"
    
    # Initialize all components
    source = OpenCVVideoSource(video_path, camera_id, settings.PROCESS_EVERY_N_FRAMES)
    vehicle_detector = YOLOVehicleDetector(settings.VEHICLE_MODEL_PATH, settings.VEHICLE_CONF_THRESHOLD)
    tracker = ByteTrackTracker(camera_id, track_max_age=settings.TRACK_MAX_AGE)
    
    plate_detector = RoboflowPlateDetector(
        api_key=os.getenv("ROBOFLOW_API_KEY"), 
        model_id=os.getenv("ROBOFLOW_MODEL_ID"),
        conf_threshold=settings.PLATE_CONF_THRESHOLD
    )
    
    # NEW: Initialize our analyzer
    analyzer = PlateQualityAnalyzer(
        min_width=int(os.getenv("PLATE_MIN_WIDTH", 60)),
        min_height=int(os.getenv("PLATE_MIN_HEIGHT", 20)),
        blur_threshold=float(os.getenv("BLUR_THRESHOLD", 100.0)),
        min_quality=float(os.getenv("MIN_PLATE_QUALITY", 0.4))
    )
    
    print("\n--- Starting Quality Assessment Pipeline ---")
    
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
                        # NEW: Analyze quality before doing anything else
                        quality = analyzer.analyze(roi, plate)
                        
                        status = "✅ USABLE" if quality.is_usable else f"❌ REJECTED ({quality.rejection_reason})"
                        
                        print(f"  -> Track {track.local_track_id} ({track.vehicle_type}): "
                              f"Plate Confidence {plate.confidence:.2f} | "
                              f"Sharpness {quality.sharpness:.1f} | "
                              f"Size {quality.width}x{quality.height} | {status}")
                        
        frames_processed += 1
        if frames_processed >= 3: 
            break
            
    source.release()

if __name__ == "__main__":
    test_pipeline()