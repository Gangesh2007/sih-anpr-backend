from typing import List, Optional
from app.schemas.observation import PlateObservation, AggregatedPlateResult

class OCRAggregator:
    @staticmethod
    def aggregate(observations: List[PlateObservation]) -> Optional[AggregatedPlateResult]:
        if not observations:
            return None
            
        scores = {}
        frames_map = {}
        
        for obs in observations:
            # RELAXED FILTER: Allow fragments of at least 2 characters for testing
            if not obs.normalized_text or len(obs.normalized_text) < 2:
                continue
                
            # Weight = OCR confidence * Plate Detection Confidence * Quality
            weight = obs.ocr_confidence * obs.plate_detection_confidence * obs.quality_score
            
            text = obs.normalized_text
            if text not in scores:
                scores[text] = 0.0
                frames_map[text] = []
                
            scores[text] += weight
            frames_map[text].append(obs.frame_number)
            
        if not scores:
            return None
            
        # Find the text variant with the highest combined weight
        best_text = max(scores.items(), key=lambda x: x[1])[0]
        best_frames = frames_map[best_text]
        
        # Calculate the average OCR confidence of the winning text
        winning_obs = [o for o in observations if o.normalized_text == best_text]
        avg_conf = sum(o.ocr_confidence for o in winning_obs) / len(winning_obs)
        
        return AggregatedPlateResult(
            plate_number=best_text,
            confidence=avg_conf,
            observation_count=len(best_frames),
            supporting_frames=best_frames
        )