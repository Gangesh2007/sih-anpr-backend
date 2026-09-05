# test_tracking.py
from app.preprocessing.video_source import OpenCVVideoSource
from app.detection.vehicle_detector import YOLOVehicleDetector
from app.tracking.bytetrack_tracker import ByteTrackTracker
from app.core.config import settings
from app.schemas.track import TrackStatus
from app.preprocessing.roi import VehicleROI

def test_pipeline():
    video_path = "data/videos/test_video.mp4"
    camera_id = "CAM_01"
    
    source = OpenCVVideoSource(video_path, camera_id, settings.PROCESS_EVERY_N_FRAMES)
    detector = YOLOVehicleDetector(settings.VEHICLE_MODEL_PATH, settings.VEHICLE_CONF_THRESHOLD)
    tracker = ByteTrackTracker(camera_id, track_max_age=settings.TRACK_MAX_AGE)
    
    print("\n--- Starting Tracking & ROI Pipeline ---")
    
    frames_processed = 0
    for frame in source.get_frames():
        # 1. Detect
        detections = detector.detect(frame)
        # 2. Track
        tracks = tracker.update(frame, detections)
        
        print(f"\nFrame {frame.frame_number} | Time: {frame.timestamp:.2f}s | Tracks: {len(tracks)}")
        
        # 3. Extract ROIs
        rois = []
        for track in tracks:
            print(f"  -> Track ID: {track.local_track_id} | Type: {track.vehicle_type.upper():<10} | Status: {track.status.value}")
            
            # We only crop images for vehicles currently on screen (NEW or ACTIVE)
            if track.status in [TrackStatus.NEW, TrackStatus.ACTIVE]:
                x1, y1, x2, y2 = map(int, track.last_bbox)
                
                # Clip coordinates to frame boundaries to prevent numpy array errors
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.width, x2), min(frame.height, y2)
                
                if x2 > x1 and y2 > y1:
                    roi_image = frame.image[y1:y2, x1:x2]
                    rois.append(VehicleROI(
                        camera_id=camera_id, track_id=track.local_track_id,
                        frame_number=frame.frame_number, timestamp=frame.timestamp,
                        bbox=[x1, y1, x2, y2], image=roi_image
                    ))
                    
        print(f"  -> Extracted {len(rois)} valid Vehicle ROI crops for plate detection.")
        
        frames_processed += 1
        if frames_processed >= 5: 
            break
            
    source.release()

if __name__ == "__main__":
    test_pipeline()