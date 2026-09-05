# app/api/cameras.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.session import get_db
from app.database.models.core_models import Camera
from app.schemas.camera import CameraCreate, CameraResponse

router = APIRouter()

@router.post("/", response_model=CameraResponse)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    db_camera = db.query(Camera).filter(Camera.id == camera.id).first()
    if db_camera:
        raise HTTPException(status_code=400, detail="Camera already registered")
    
    new_camera = Camera(**camera.model_dump())
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    return new_camera

@router.get("/", response_model=List[CameraResponse])
def get_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()