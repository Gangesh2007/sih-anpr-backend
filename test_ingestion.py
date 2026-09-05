# test_ingestion.py
from app.preprocessing.video_source import OpenCVVideoSource
from app.core.config import settings

def test_pipeline():
    # Replace with path to a real MP4 file on your machine
    video_path = "data/videos/test_video.mp4" 
    camera_id = "CAM_01"
    
    try:
        source = OpenCVVideoSource(
            source_path=video_path, 
            camera_id=camera_id, 
            process_every_n_frames=settings.PROCESS_EVERY_N_FRAMES
        )
        
        print(f"Starting ingestion. Processing 1 frame every {settings.PROCESS_EVERY_N_FRAMES} frames.")
        
        frames_processed = 0
        for frame in source.get_frames():
            print(f"Read Frame: {frame.frame_number} | Time: {frame.timestamp:.2f}s | Resolution: {frame.width}x{frame.height}")
            frames_processed += 1
            
            # Stop early just for this test
            if frames_processed >= 5:
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        source.release()

if __name__ == "__main__":
    test_pipeline()