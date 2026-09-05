# test_plate_detector.py
from app.preprocessing.video_source import OpenCVVideoSource
from app.detection.vehicle_detector import YOLOVehicleDetector
from app.tracking.bytetrack_tracker import ByteTrackTracker
from app.detection.roboflow_plate_detector import RoboflowPlateDetector
from app.core.config import settings
from app.schemas.track import TrackStatus
from app.preprocessing.roi import VehicleROI

def test_pipeline():
    video_path = "data/videos/test_video.mp4"
    camera_id = "CAM_01"
    
    source = OpenCVVideoSource(video_path, camera_id, settings.PROCESS_EVERY_N_FRAMES)
    vehicle_detector = YOLOVehicleDetector(settings.VEHICLE_MODEL_PATH, settings.VEHICLE_CONF_THRESHOLD)
    tracker = ByteTrackTracker(camera_id, track_max_age=settings.TRACK_MAX_AGE)
    plate_detector = RoboflowPlateDetector(
        api_key=settings.ROBOFLOW_API_KEY, 
        model_id=settings.ROBOFLOW_MODEL_ID,
        conf_threshold=settings.PLATE_CONF_THRESHOLD
    )
    
    print("\n--- Starting Full Detection Pipeline ---")
    
    frames_processed = 0
    for frame in source.get_frames():
        # 1. Detect Vehicles & Track
        detections = vehicle_detector.detect(frame)
        tracks = tracker.update(frame, detections)
        
        print(f"\nFrame {frame.frame_number} | Time: {frame.timestamp:.2f}s")
        
        # 2. Extract ROIs and Detect Plates
        for track in tracks:
            if track.status in [TrackStatus.NEW, TrackStatus.ACTIVE]:
                x1, y1, x2, y2 = map(int, track.last_bbox)
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.width, x2), min(frame.height, y2)
                
                # Ensure the crop is valid
                if x2 > x1 and y2 > y1:
                    roi_image = frame.image[y1:y2, x1:x2]
                    roi = VehicleROI(
                        camera_id=camera_id, track_id=track.local_track_id,
                        frame_number=frame.frame_number, timestamp=frame.timestamp,
                        bbox=[x1, y1, x2, y2], image=roi_image
                    )
                    
                    # 3. Detect License Plate inside the Vehicle ROI
                    plate = plate_detector.detect(roi)
                    
                    if plate:
                        print(f"  -> Track {track.local_track_id} ({track.vehicle_type}): PLATE DETECTED [Conf: {plate.confidence:.2f}]")
                        
        frames_processed += 1
        if frames_processed >= 3: # Stop after 3 frames to save API calls
            break
            
    source.release()

if __name__ == "__main__":
    test_pipeline()