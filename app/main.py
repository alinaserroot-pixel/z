"""Main application entry point"""

import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os

from app.api.routes import router
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Registration Automation Tool",
    description="أداة أتمتة التسجيل في المواقع - Automate website registration",
    version="0.1.0"
)

# Include API routes
app.include_router(router)

# Create templates directory if it doesn't exist
template_dir = Path(__file__).parent / "templates"
os.makedirs(template_dir, exist_ok=True)


@app.get("/")
async def root():
    """Serve the main page"""
    return FileResponse(template_dir / "index.html", media_type="text/html")


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "registration-automation",
        "version": "0.1.0",
        "dry_run_mode": settings.dry_run
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
