import os
import base64
import json
import re
import logging
import aiofiles
import pathlib # Import pathlib
import tempfile
import cv2 # For extracting frames from videos
import numpy as np
import subprocess
import ffmpeg # FFmpeg Python bindings for enhanced video processing
from typing import List, Dict, Optional, Any
import shutil

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError, APIStatusError, APIConnectionError, AuthenticationError

# Import OpenAI client utilities
from utils import openai_client
from utils.media_analysis import analyze_media, extract_frames_and_analyze_video, analyze_frames
from utils.story_generation import (
    generate_story_from_image,
    generate_story_from_multiple_images, 
    generate_story_from_video,
    parse_openai_response
)
from utils.prompts import STORY_GENERATION_PROMPT

# --- Configuration & Setup --- 

# Get the directory where main.py is located
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
# Construct the path to the .env file
DOTENV_PATH = SCRIPT_DIR / ".env"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file in the script's directory
# Use override=True to ensure .env takes precedence over system variables
try:
    if DOTENV_PATH.is_file():
        logger.info(f"Loading environment variables from: {DOTENV_PATH}")
        load_dotenv(dotenv_path=DOTENV_PATH, override=True)
    else:
        logger.warning(f".env file not found at {DOTENV_PATH}. Relying on system environment variables.")
        load_dotenv(override=True) # Attempt to load from default locations or just use system vars
except Exception as e:
    logger.error(f"Error loading environment variables: {e}")
    # Continue execution, but log the error

# Create uploads directory if it doesn't exist
UPLOAD_DIR = SCRIPT_DIR / "uploads"
try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    logger.error(f"Error creating upload directory: {e}")
    # This is a critical error, but we'll continue and let it fail when accessed

# --- FastAPI App Setup --- 
app = FastAPI(title="Media Analysis Story Generator API")

# CORS Configuration (Allow frontend origin)
# Adjust origins as needed for deployment
origins = [
    "http://localhost",
    "http://localhost:8000", # Default FastAPI dev server
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    # Add other origins if needed, e.g., deployed frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"]
)

# Mount static files (CSS, JS)
try:
    app.mount("/static", StaticFiles(directory=SCRIPT_DIR / "static"), name="static")
except Exception as e:
    logger.error(f"Error mounting static files: {e}")
    # This is a warning, but we'll continue as API endpoints may still work

# --- FastAPI Lifecycle Events ---

@app.on_event("startup")
async def startup_event():
    """Initialize resources on application startup"""
    logger.info("Application starting up, initializing OpenAI client...")
    try:
        openai_client.initialize_openai_client()
    except Exception as e:
        logger.error(f"Error initializing OpenAI client: {e}")
        # The application will continue but may not work correctly

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on application shutdown"""
    logger.info("Application shutting down, cleaning up resources...")
    try:
        openai_client.cleanup_client()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# --- API Endpoints --- 

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serves the main HTML page."""
    index_html_path = SCRIPT_DIR / "static" / "index.html"
    if not index_html_path.is_file():
        logger.error(f"Frontend HTML file not found at: {index_html_path}")
        raise HTTPException(status_code=500, detail="Internal server error: Frontend not found.")
    try:
        async with aiofiles.open(index_html_path, mode='r') as f:
            content = await f.read()
        return HTMLResponse(content=content)
    except Exception as e:
        logger.exception(f"Error reading frontend HTML file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error: Could not load frontend.")

@app.post("/analyze/")
async def analyze_media_endpoint(
    files: List[UploadFile] = File(..., description="Media files (JPG, PNG images or MP4 video)"),
    prompt: Optional[str] = Form(None) # Make prompt optional
):
    """
    Endpoint to receive media files and an optional prompt for analysis.
    Supports JPG, PNG images (multiple allowed) or a single MP4 video.
    Maximum file size: 10MB per image, 50MB for video.
    
    Delegates the core logic to the analyze_media function.
    """
    try:
        # Pass empty string if prompt is None
        result = await analyze_media(files=files, prompt=prompt or "") 
        return JSONResponse(content=result)
    except HTTPException as e:
        # Re-raise known HTTP exceptions from analyze_media
        raise e
    except OpenAIError as e:
        # Handle OpenAI errors specifically if they bubble up unexpectedly
        logger.error(f"OpenAI API error in endpoint: {e}")
        detail = f"OpenAI API Error: {e.message}" if hasattr(e, 'message') else str(e)
        status_code = e.status_code if hasattr(e, 'status_code') else 503
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e:
        # Catch any other unexpected errors during endpoint processing
        logger.exception("An unexpected error occurred in the /analyze endpoint.")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    try:
        # Use reload=True for development
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}") 