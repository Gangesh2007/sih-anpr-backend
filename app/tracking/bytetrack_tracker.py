# app/tracking/bytetrack_tracker.py
import supervision as sv
import numpy as np
from typing import List, Dict
from app.tracking.base import Tracker
from app.detection.base import VehicleDetection
from app.preprocessing.frame import Frame
from app.schemas.track import TrackState, TrackStatus

# COCO mappings
TARGET_CLASSES = {2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

class ByteTrackTracker(Tracker):
    def __init__(self, camera_id: str, track_max_age: int = 30):
        self.camera_id = camera_id
        # match_thresh determines how strictly a bbox must overlap to be the same vehicle
        self.tracker = sv.ByteTrack(lost_track_buffer=track_max_age, frame_rate=25)
        self.active_tracks: Dict[int, TrackState] = {}
        
    def update(self, frame: Frame, detections: List[VehicleDetection]) -> List[TrackState]:
        if not detections:
            sv_detections = sv.Detections.empty()
        else:
            # Convert our detections to supervision format
            xyxy = np.array([d.bbox for d in detections], dtype=np.float32)
            confidence = np.array([d.confidence for d in detections], dtype=np.float32)
            class_id = np.array([d.class_id for d in detections], dtype=int)
            
            sv_detections = sv.Detections(
                xyxy=xyxy, confidence=confidence, class_id=class_id
            )
            
        tracked_detections = self.tracker.update_with_detections(sv_detections)
        current_frame_track_ids = set()
        
        # 1. Update Existing & Add New Tracks
        for i in range(len(tracked_detections)):
            bbox = tracked_detections.xyxy[i].tolist()
            track_id = int(tracked_detections.tracker_id[i])
            cls_id = int(tracked_detections.class_id[i])
            vehicle_type = TARGET_CLASSES.get(cls_id, "unknown")
            
            current_frame_track_ids.add(track_id)
            
            if track_id not in self.active_tracks:
                self.active_tracks[track_id] = TrackState(
                    camera_id=self.camera_id,
                    local_track_id=track_id,
                    first_seen=frame.timestamp,
                    last_seen=frame.timestamp,
                    last_bbox=bbox,
                    vehicle_type=vehicle_type,
                    status=TrackStatus.NEW
                )
            else:
                track = self.active_tracks[track_id]
                track.last_seen = frame.timestamp
                track.last_bbox = bbox
                track.status = TrackStatus.ACTIVE

        # 2. Manage LOST and FINISHED tracks
        for track_id, track in list(self.active_tracks.items()):
            if track_id not in current_frame_track_ids:
                time_since_last_seen = frame.timestamp - track.last_seen
                track.status = TrackStatus.LOST
                
                # If a vehicle has been lost longer than the buffer duration, purge it.
                if time_since_last_seen > (30 / 25.0):
                    track.status = TrackStatus.FINISHED
                    del self.active_tracks[track_id]

        return list(self.active_tracks.values())