# app/preprocessing/video_source.py
import cv2
import time
from abc import ABC, abstractmethod
from typing import Generator
from app.preprocessing.frame import Frame
from app.core.logging import logger

class VideoSource(ABC):
    @abstractmethod
    def get_frames(self) -> Generator[Frame, None, None]:
        """Yields sequential frames from the source."""
        pass
    
    @abstractmethod
    def release(self) -> None:
        """Frees hardware/file resources."""
        pass

class OpenCVVideoSource(VideoSource):
    def __init__(self, source_path: str, camera_id: str, process_every_n_frames: int = 1):
        self.source_path = source_path
        self.camera_id = camera_id
        self.process_every_n_frames = max(1, process_every_n_frames)
        self.cap = cv2.VideoCapture(self.source_path)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {self.source_path} for Camera {self.camera_id}")
            raise ValueError(f"Cannot open video source: {self.source_path}")
            
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25.0
        self.is_live = str(self.source_path).startswith(('rtsp://', 'http://'))
        logger.info(f"Initialized VideoSource for {self.camera_id} at {self.fps} FPS.")

    def get_frames(self) -> Generator[Frame, None, None]:
        frame_count = 0
        
        while self.cap.isOpened():
            ret, frame_data = self.cap.read()
            
            if not ret:
                logger.info(f"End of stream reached or disconnected for {self.camera_id}")
                break

            # Frame sampling logic (configurable frame skipping)
            if frame_count % self.process_every_n_frames == 0:
                # Use real wall-clock time for RTSP, calculate from frame index for MP4 testing
                timestamp = time.time() if self.is_live else (frame_count / self.fps)
                
                yield Frame(
                    camera_id=self.camera_id,
                    frame_number=frame_count,
                    timestamp=timestamp,
                    image=frame_data
                )
            
            frame_count += 1

    def release(self) -> None:
        if self.cap and self.cap.isOpened():
            self.cap.release()
            logger.info(f"Released VideoSource for {self.camera_id}")