# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "City-Wide ANPR System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: Optional[str] = None
    
    # CV & Model Configs
    VEHICLE_MODEL_PATH: str = "models/vehicle/yolov8s.pt"
    VEHICLE_CONF_THRESHOLD: float = 0.40
    
    ROBOFLOW_API_KEY: Optional[str] = None
    ROBOFLOW_MODEL_ID: str = "license-plate-recognition-rxg4e"
    PLATE_CONF_THRESHOLD: float = 0.50
    
    OCR_PROVIDER: str = "paddleocr"
    OCR_CONF_THRESHOLD: float = 0.70
    
    # System Configs
    PROCESS_EVERY_N_FRAMES: int = 3
    TRACK_MAX_AGE: int = 30
    STORAGE_PATH: str = "./data"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()