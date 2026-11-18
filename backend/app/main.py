import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database.connection import init_db
from app.routers import health, notices, deadlines, conflicts, ingest, chat, upload

app = FastAPI(
    title="CampusSage",
    description="CampusSage: AI-Powered Web Information & Opportunity Hub",
    version="2.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SQLite database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Register API Routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(notices.router)
app.include_router(deadlines.router)
app.include_router(conflicts.router)
app.include_router(ingest.router)

# Mount Frontend Static Files
FRONTEND_DIR = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "frontend", "public"))

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"message": "CampusSage API is running. index.html not found in frontend/public."}
else:
    @app.get("/")
    def root():
        return {"message": "CampusSage Backend API is active.", "docs_url": "/docs"}
