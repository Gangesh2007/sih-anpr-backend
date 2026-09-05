# app/pipeline/video_processor.py
import os
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
from app.matching.global_identity import GlobalIdentityResolver
from app.services.alert_service import AlertService

# Database
from app.database.session import SessionLocal
from app.database.models.core_models import Track, PlateObservation as DBPlateObservation, Camera
from app.core.logging import logger

class VideoProcessor:
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self.vehicle_detector = YOLOVehicleDetector(settings.VEHICLE_MODEL_PATH, settings.VEHICLE_CONF_THRESHOLD)
        self.tracker = ByteTrackTracker(camera_id, track_max_age=settings.TRACK_MAX_AGE)
        self.plate_detector = RoboflowPlateDetector(
            os.getenv("ROBOFLOW_API_KEY"), 
            os.getenv("ROBOFLOW_MODEL_ID"), 
            settings.PLATE_CONF_THRESHOLD
        )
        self.analyzer = PlateQualityAnalyzer(
            min_width=int(os.getenv("PLATE_MIN_WIDTH", 15)),
            min_height=int(os.getenv("PLATE_MIN_HEIGHT", 5)),
            blur_threshold=float(os.getenv("BLUR_THRESHOLD", 50.0)),
            min_quality=float(os.getenv("MIN_PLATE_QUALITY", 0.4))
        )
        self.preprocessor = PlatePreprocessor()
        self.ocr_engine = PaddleOCREngine(conf_threshold=settings.OCR_CONF_THRESHOLD)
        self.alert_service = AlertService()

    def process_stream(self, video_path: str, max_frames: int = None):
        source = OpenCVVideoSource(video_path, self.camera_id, settings.PROCESS_EVERY_N_FRAMES)
        logger.info(f"Starting processing for camera {self.camera_id}")
        
        db = SessionLocal()
        try:
            cam = db.query(Camera).filter(Camera.id == self.camera_id).first()
            if not cam:
                logger.error(f"Camera {self.camera_id} not found in database. Please register it first.")
                return

            frames_processed = 0
            for frame in source.get_frames():
                detections = self.vehicle_detector.detect(frame)
                tracks = self.tracker.update(frame, detections)
                
                for track in tracks:
                    if track.status in [TrackStatus.NEW, TrackStatus.ACTIVE]:
                        self._process_active_track(frame, track)
                    elif track.status == TrackStatus.LOST and track.plate_observations:
                        self._finalize_track(db, track)
                        track.plate_observations.clear() # Prevent duplicate saves
                        
                frames_processed += 1
                if max_frames and frames_processed >= max_frames:
                    break
            
            # --- NEW: END OF STREAM FLUSH ---
            logger.info("Video stream ended. Flushing remaining active tracks to database...")
            for track in self.tracker.active_tracks.values():
                if track.plate_observations:
                    self._finalize_track(db, track)
                    track.plate_observations.clear()
            # --------------------------------

        finally:
            source.release()
            db.close()
            logger.info(f"Finished processing stream for {self.camera_id}")


    def _process_active_track(self, frame, track):
        x1, y1, x2, y2 = map(int, track.last_bbox)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.width, x2), min(frame.height, y2)
        
        if x2 > x1 and y2 > y1:
            roi = VehicleROI(
                camera_id=self.camera_id, track_id=track.local_track_id,
                frame_number=frame.frame_number, timestamp=frame.timestamp,
                bbox=[x1, y1, x2, y2], image=frame.image[y1:y2, x1:x2]
            )
            
            plate = self.plate_detector.detect(roi)
            if plate:
                quality = self.analyzer.analyze(roi, plate)
                if quality.is_usable:
                    px1, py1 = max(0, int(plate.bbox[0])), max(0, int(plate.bbox[1]))
                    px2, py2 = min(roi.image.shape[1], int(plate.bbox[2])), min(roi.image.shape[0], int(plate.bbox[3]))
                    raw_plate = roi.image[py1:py2, px1:px2]
                    enhanced = self.preprocessor.preprocess(raw_plate)
                    ocr = self.ocr_engine.recognize(enhanced)
                    
                    if ocr.normalized_text:
                        obs = PlateObservation(
                            frame_number=frame.frame_number, timestamp=frame.timestamp,
                            raw_text=ocr.raw_text, normalized_text=ocr.normalized_text,
                            ocr_confidence=ocr.confidence, plate_detection_confidence=plate.confidence,
                            quality_score=quality.quality_score
                        )
                        track.plate_observations.append(obs)

    def _finalize_track(self, db, track):
        final_result = OCRAggregator.aggregate(track.plate_observations)
        if not final_result:
            return

        logger.info(f"Saving Track {track.local_track_id} to DB with Plate: {final_result.plate_number}")
        
        # Save the Track
        db_track = Track(
            camera_id=self.camera_id,
            local_track_id=track.local_track_id,
            first_seen=track.first_seen,
            last_seen=track.last_seen,
            vehicle_type=track.vehicle_type,
            vehicle_color=track.vehicle_color,
            status=track.status.value
        )
        db.add(db_track)
        db.flush() # Flush to get the auto-incremented Track ID

        # Save the aggregated Observation
        # ... existing code in _finalize_track ...
        db_obs = DBPlateObservation(
            track_id=db_track.id,
            frame_number=track.plate_observations[-1].frame_number,
            timestamp=track.plate_observations[-1].timestamp,
            plate_text_raw=final_result.plate_number, 
            plate_number_normalized=final_result.plate_number,
            ocr_confidence=final_result.confidence,
            plate_detection_confidence=track.plate_observations[-1].plate_detection_confidence,
            quality_score=track.plate_observations[-1].quality_score
        )
        db.add(db_obs)
        db.commit() # Commit the local track data first

        # NEW: Resolve Global Identity
        GlobalIdentityResolver.resolve_and_store(
            db=db,
            track=db_track,
            plate_text=final_result.plate_number,
            plate_conf=final_result.confidence
        )

        # Check against Redis Watchlist
        self.alert_service.check_and_alert(
            plate_number=final_result.plate_number,
            camera_id=self.camera_id,
            confidence=final_result.confidence
        )