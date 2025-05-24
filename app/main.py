import os
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import shutil
from pathlib import Path
import uuid

from app.orchestrator import Orchestrator

# Initialize FastAPI app
app = FastAPI(
    title="PersonaAnalyst API",
    description="API for analyzing and managing person profiles and meeting data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = Orchestrator()

# Create upload directory
UPLOAD_DIR = Path("./data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Pydantic models for request/response
class ProfileCreate(BaseModel):
    full_name: str

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    created_at: str
    meetings_count: int

# Helper function to save uploaded file
async def save_upload_file(upload_file: UploadFile) -> str:
    """Save uploaded file and return its path."""
    try:
        # Generate unique filename
        file_extension = Path(upload_file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
        
        return str(file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    finally:
        upload_file.file.close()

# API endpoints
@app.post("/profiles", response_model=ProfileResponse)
async def create_profile(profile: ProfileCreate):
    """Create a new profile."""
    try:
        result = await orchestrator.create_profile(profile.full_name)
        return {
            "id": result["id"],
            "full_name": result["full_name"],
            "created_at": result["created_at"],
            "meetings_count": len(result["meetings"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles", response_model=List[ProfileResponse])
async def list_profiles():
    """List all profiles."""
    try:
        return orchestrator.list_profiles()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/{profile_id}")
async def get_profile(profile_id: str):
    """Get detailed profile information."""
    try:
        profile = orchestrator.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a profile and all associated data."""
    try:
        orchestrator.delete_profile(profile_id)
        return JSONResponse(content={"message": "Profile deleted successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/{profile_id}/meetings")
async def process_meeting(profile_id: str, video: UploadFile = File(...)):
    """Process a meeting video and add it to a profile."""
    try:
        # Validate file type
        if not video.filename.endswith('.mp4'):
            raise HTTPException(
                status_code=400,
                detail="Only MP4 video files are supported"
            )
        
        # Save uploaded file
        video_path = await save_upload_file(video)
        
        # Process meeting
        result = await orchestrator.process_meeting(profile_id, video_path)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/{profile_id}/chat")
async def chat(profile_id: str, request: ChatRequest):
    """Process a chat query about a profile."""
    try:
        result = await orchestrator.chat(
            profile_id,
            request.query,
            request.conversation_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"} 