# app/api/jobs.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
import os
from app.pipeline.video_processor import VideoProcessor
from app.core.logging import logger

router = APIRouter()

class JobCreate(BaseModel):
    camera_id: str
    video_path: str

def run_video_processing_task(camera_id: str, video_path: str):
    """The background worker function that executes the CV pipeline."""
    try:
        processor = VideoProcessor(camera_id=camera_id)
        # Note: We omit max_frames so it processes the entire video
        processor.process_stream(video_path=video_path)
    except Exception as e:
        logger.error(f"Background task failed for camera {camera_id}: {e}")

@router.post("/process-video")
async def process_video(job: JobCreate, background_tasks: BackgroundTasks):
    if not os.path.exists(job.video_path):
        raise HTTPException(status_code=404, detail="Video file not found on server")
        
    # Queue the heavy CV processing to run in the background
    background_tasks.add_task(run_video_processing_task, job.camera_id, job.video_path)
    
    return {
        "status": "Accepted", 
        "message": f"Processing job for {job.camera_id} queued successfully in the background."
    }