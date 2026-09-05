# app/database/models/core_models.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.session import Base

class Camera(Base):
    __tablename__ = "cameras"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    location_name = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    camera_id = Column(String, ForeignKey("cameras.id"), index=True)
    local_track_id = Column(Integer, index=True)
    first_seen = Column(Float)
    last_seen = Column(Float)
    vehicle_type = Column(String)
    vehicle_color = Column(String, default="unknown")
    status = Column(String)
    
    # Relationships
    observations = relationship("PlateObservation", back_populates="track")

class PlateObservation(Base):
    __tablename__ = "plate_observations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)
    frame_number = Column(Integer)
    timestamp = Column(Float, index=True)
    
    plate_text_raw = Column(String)
    plate_number_normalized = Column(String, index=True)
    
    ocr_confidence = Column(Float)
    plate_detection_confidence = Column(Float)
    quality_score = Column(Float)
    
    # Relationships
    track = relationship("Track", back_populates="observations")

import uuid

def generate_uuid():
    return f"V-{uuid.uuid4().hex[:8].upper()}"

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    plate_number = Column(String, index=True)
    plate_confidence = Column(Float)
    vehicle_type = Column(String)
    vehicle_color = Column(String, default="unknown")
    first_seen = Column(Float)
    last_seen = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    observations = relationship("VehicleObservation", back_populates="vehicle")

class VehicleObservation(Base):
    __tablename__ = "vehicle_observations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    vehicle_id = Column(String, ForeignKey("vehicles.id"), index=True)
    camera_id = Column(String, ForeignKey("cameras.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"), unique=True)
    timestamp = Column(Float, index=True)
    frame_number = Column(Integer)
    confidence = Column(Float)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="observations")