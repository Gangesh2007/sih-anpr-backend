# app/api/health.py
from fastapi import APIRouter
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()

@router.get("/health", response_model=dict)
async def health_check():
    logger.info("Health check endpoint accessed.")
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }