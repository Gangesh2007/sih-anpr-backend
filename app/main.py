from dotenv import load_dotenv
load_dotenv()  # MUST be called before importing our app modules

# app/main.py
from fastapi import FastAPI
from app.core.config import settings
from app.core.logging import logger
from app.api import health, cameras, search, trajectories, watchlist, alerts, jobs  # <-- NEW import

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )

    # Include Routers
    app.include_router(health.router, tags=["Health"])
    
    # <-- NEW: Attach the new routers
    app.include_router(cameras.router, prefix=f"{settings.API_V1_STR}/cameras", tags=["Cameras"])
    app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search"])

    app.include_router(trajectories.router, prefix=f"{settings.API_V1_STR}/trajectories", tags=["Trajectories"])

    # <-- NEW: Attach Watchlist and WebSocket routes
    app.include_router(watchlist.router, prefix=f"{settings.API_V1_STR}/watchlist", tags=["Watchlist"])

    # WebSockets usually sit at a top-level /ws prefix rather than /api/v1
    app.include_router(alerts.router, prefix="/alerts", tags=["Real-Time Alerts"])

    # <-- NEW: Attach Jobs router
    app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])

    @app.on_event("startup")
    async def startup_event():
        logger.info(f"Starting up {settings.PROJECT_NAME} v{settings.VERSION}")
        logger.info("Configuration loaded successfully.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down ANPR backend.")

    return app

app = create_app()