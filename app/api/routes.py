"""API routes"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from app.models.registration import (
    RegistrationRequest,
    RegistrationResponse,
    RegistrationHistory
)
from app.services.registration_service import RegistrationService
from datetime import datetime

router = APIRouter(prefix="/api", tags=["registration"])
service = RegistrationService()


@router.post("/register", response_model=dict)
async def register(
    request: RegistrationRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a new registration process
    """
    try:
        registration_id = await service.process_registration(request)
        return {
            "id": registration_id,
            "status": "pending",
            "message": "Registration process started"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/registration/{registration_id}", response_model=dict)
async def get_registration(registration_id: str):
    """
    Get registration status
    """
    registration = service.get_registration(registration_id)
    
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")
    
    return {
        "id": registration["id"],
        "website_url": registration["website_url"],
        "email": registration["email"],
        "status": registration["status"],
        "message": registration["message"],
        "error_reason": registration["error_reason"],
        "created_at": registration["created_at"],
        "completed_at": registration["completed_at"]
    }


@router.get("/history", response_model=list)
async def get_history(limit: int = 50):
    """
    Get registration history
    """
    history = service.get_history(limit)
    
    return [
        {
            "id": h["id"],
            "website_url": h["website_url"],
            "email": h["email"],
            "status": h["status"],
            "message": h["message"],
            "error_reason": h["error_reason"],
            "created_at": h["created_at"],
            "completed_at": h["completed_at"]
        }
        for h in history
    ]


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok", "service": "registration-automation"}
