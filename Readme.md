# Distributed ANPR & Vehicle Tracking Backend

A high-performance, modular backend for a city-wide distributed Automatic Number Plate Recognition (ANPR) and vehicle tracking system. Built for SIH 2026.

## Architecture & Tech Stack
* **Framework:** FastAPI (Python)
* **Database:** PostgreSQL with SQLAlchemy ORM and Alembic migrations
* **Computer Vision Pipeline:** OpenCV, YOLOv26 (Vehicle Detection), ByteTrack (Association), Roboflow (Plate Detection), PaddleOCR (Optical Character Recognition)
* **Real-Time Engine:** WebSockets for instant watchlist alerts
* **Concurrency:** FastAPI Background Tasks for long-running video stream processing

## Core Features
* **Intelligent Quality Gating:** Rejects blurry or undersized plates using OpenCV Laplacian variance before wasting OCR compute.
* **Temporal Aggregation:** Consolidates multiple messy frame-by-frame OCR reads into a single high-confidence string when a vehicle leaves the frame.
* **Global Vehicle Identity:** Uses spatial and temporal heuristics to link local camera tracks to city-wide unique vehicle identifiers (e.g., `V-1042`).
* **Trajectory Generation:** Chronologically maps a vehicle's path across multiple cameras, calculating physical distance and travel duration.
* **Real-Time Watchlist Alerts:** In-memory $O(1)$ lookup engine pushes immediate WebSocket broadcasts when a flagged vehicle is detected.

## Prerequisites
* Python 3.10+
* PostgreSQL (Running locally or via Docker/WSL)
* C++ Build Tools (Required for PaddleOCR)

## Local Setup

**1. Clone the repository and setup the virtual environment:**
```powershell
git clone [https://github.com/Gangesh2007/sih-anpr-backend.git](https://github.com/Gangesh2007/sih-anpr-backend.git)
cd sih-anpr-backend
python -m venv venv
.\venv\Scripts\activate
```

**2. Install dependencies:**
```powershell
pip install -r requirements.txt
```

**3. Configure Environment Variables:**
Create a `.env` file in the root directory and add the following:
```env
# Database
DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/anpr_db"

# API Keys
ROBOFLOW_API_KEY="your_api_key_here"
ROBOFLOW_MODEL_ID="license-plate-recognition-rxg4e/4"

# CV Thresholds
VEHICLE_CONF_THRESHOLD=0.5
PLATE_CONF_THRESHOLD=0.5
OCR_CONF_THRESHOLD=0.70

# Quality Gating
PLATE_MIN_WIDTH=15
PLATE_MIN_HEIGHT=5
BLUR_THRESHOLD=50.0
MIN_PLATE_QUALITY=0.4
```

**4. Setup the Database:**
Ensure your PostgreSQL server is running and the `anpr_db` database is created.
```powershell
alembic upgrade head
```

## Running the Application
Start the FastAPI server:
```powershell
uvicorn app.main:app --reload
```
Access the interactive Swagger API documentation at: `http://localhost:8000/docs`
