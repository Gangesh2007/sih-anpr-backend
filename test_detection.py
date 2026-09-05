# test_detection.py
from app.preprocessing.video_source import OpenCVVideoSource
from app.detection.vehicle_detector import YOLOVehicleDetector
from app.core.config import settings

def test_pipeline():
    video_path = "data/videos/test_video.mp4"
    camera_id = "CAM_01"
    
    try:
        source = OpenCVVideoSource(
            source_path=video_path, 
            camera_id=camera_id, 
            process_every_n_frames=settings.PROCESS_EVERY_N_FRAMES
        )
        
        detector = YOLOVehicleDetector(
            model_path=settings.VEHICLE_MODEL_PATH,
            conf_threshold=settings.VEHICLE_CONF_THRESHOLD
        )
        
        print("\n--- Starting Detection Pipeline ---")
        
        frames_processed = 0
        for frame in source.get_frames():
            detections = detector.detect(frame)
            
            print(f"Frame {frame.frame_number} | Time: {frame.timestamp:.2f}s | Vehicles Found: {len(detections)}")
            for d in detections:
                print(f"  -> {d.class_name.upper()} ({d.confidence:.2f}) at [{int(d.bbox[0])}, {int(d.bbox[1])}, {int(d.bbox[2])}, {int(d.bbox[3])}]")
            
            frames_processed += 1
            if frames_processed >= 3:  # Just test 3 frames
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        source.release()

if __name__ == "__main__":
    test_pipeline()