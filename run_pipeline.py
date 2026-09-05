# run_pipeline.py
import os
from dotenv import load_dotenv
load_dotenv()

from app.pipeline.video_processor import VideoProcessor

if __name__ == "__main__":
    # Use the camera ID you created via the Swagger API earlier
    CAMERA_ID = "CAM_01"
    VIDEO_PATH = "data/videos/test_video.mp4"
    
    processor = VideoProcessor(camera_id=CAMERA_ID)
    
    # We limit to 30 frames for testing, but remove max_frames for full videos
    processor.process_stream(video_path=VIDEO_PATH)