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

# --- Configuration & Setup --- 

# Get the directory where main.py is located
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
# Construct the path to the .env file
DOTENV_PATH = SCRIPT_DIR / ".env"

# Load environment variables from .env file in the script's directory
# Use override=True to ensure .env takes precedence over system variables
logger = logging.getLogger(__name__) # Get logger early for dotenv status
if DOTENV_PATH.is_file():
    logger.info(f"Loading environment variables from: {DOTENV_PATH}")
    load_dotenv(dotenv_path=DOTENV_PATH, override=True)
else:
    logger.warning(f".env file not found at {DOTENV_PATH}. Relying on system environment variables.")
    load_dotenv(override=True) # Attempt to load from default locations or just use system vars

# Configure logging (can be done after loading .env if log level is set there)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__) # Logger already initialized above

# Create uploads directory if it doesn't exist
UPLOAD_DIR = SCRIPT_DIR / "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# OpenAI Configuration (Now reliably loaded from .env if present and overriding)
API_KEY = os.getenv("OPENAI_API_KEY")
ORG_ID = os.getenv("OPENAI_ORG_ID")

# Model selection (similar logic to TS example)
# Use gpt-4.1-mini as requested in custom instructions
VISION_MODEL = "gpt-4.1-mini" 
FALLBACK_VISION_MODEL = "gpt-4.1-mini" # Fallback if preferred is unavailable, but mini should be available
active_vision_model = VISION_MODEL
using_fallback_mode = False # Flag if API key is invalid or models unavailable

# Initialize OpenAI client (will be done after validation)
client: Optional[OpenAI] = None

# Validate API Key and setup OpenAI client
def initialize_openai_client():
    global client, active_vision_model, using_fallback_mode

    if not API_KEY:
        logger.error("❌ OPENAI_API_KEY environment variable is not set. Falling back.")
        using_fallback_mode = True
        return

    key_preview = f"{API_KEY[:7]}...{API_KEY[-4:]}"
    is_project_based_key = API_KEY.startswith("sk-proj-")
    logger.info(f"OpenAI API key detected: {key_preview} ({'project-based' if is_project_based_key else 'standard'})")

    try:
        client = OpenAI(
            api_key=API_KEY,
            organization=ORG_ID, # Will be None if not set
            default_headers={"OpenAI-Beta": "assistants=v1"} # As per TS example
        )

        # Test API key with a simple call
        logger.info(f"Attempting to validate API key and check model: {VISION_MODEL}")
        # Using a simple, low-cost call for validation
        client.models.retrieve(VISION_MODEL) 
        logger.info(f"✅ OpenAI API key validated successfully. Using vision model: {VISION_MODEL}")
        active_vision_model = VISION_MODEL
        using_fallback_mode = False

    except AuthenticationError as e:
        logger.error(f"❌ AUTHENTICATION ERROR: Invalid OpenAI API key or insufficient permissions. Status: {e.status_code}. Message: {e.message}")
        if is_project_based_key:
            logger.error("Project-based keys (sk-proj-*) may have limited permissions. Check model access in your OpenAI project settings.")
        else:
            logger.error("Verify your API key at https://platform.openai.com/account/api-keys")
        client = None
        using_fallback_mode = True
    except APIStatusError as e:
        # Handle cases like model not found or other API errors during validation
        logger.error(f"❌ API ERROR during validation: Status {e.status_code}. Message: {e.message}")
        if e.code == 'model_not_found':
            logger.warning(f"Model '{VISION_MODEL}' not found or not accessible with this key. Trying fallback '{FALLBACK_VISION_MODEL}'.")
            try:
                client.models.retrieve(FALLBACK_VISION_MODEL)
                logger.info(f"✅ Fallback model '{FALLBACK_VISION_MODEL}' validated. Using fallback.")
                active_vision_model = FALLBACK_VISION_MODEL
                using_fallback_mode = False
            except Exception as fallback_e:
                logger.error(f"❌ Fallback model '{FALLBACK_VISION_MODEL}' also failed validation: {fallback_e}. Enabling fallback mode.")
                client = None
                using_fallback_mode = True
        else:
             client = None
             using_fallback_mode = True # Fallback for other API errors
    except APIConnectionError as e:
        logger.error(f"❌ CONNECTION ERROR: Could not connect to OpenAI API. {e}")
        client = None
        using_fallback_mode = True
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred during OpenAI client initialization: {e}")
        client = None
        using_fallback_mode = True

# Initialize on startup
initialize_openai_client()

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
app.mount("/static", StaticFiles(directory=SCRIPT_DIR / "static"), name="static")

# --- OpenAI Interaction Functions --- 

# (Existing functions: initialize_openai_client, parse_openai_response, etc.)
# ...

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
    files: List[UploadFile] = File(...),
    prompt: Optional[str] = Form(None) # Make prompt optional
):
    """
    Endpoint to receive media files and an optional prompt for analysis.
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
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred.")

# --- Helper function for actual analysis (separated for clarity) ---
async def analyze_media(files: List[UploadFile], prompt: str) -> Dict[str, str]:
    """
    Analyzes media files using OpenAI Vision.

    Handles:
    - Single image upload
    - Multiple image uploads
    - Single video upload (metadata only)
    - Optional text prompt to guide the AI

    Returns:
    - JSON response: {"english": "...", "thai": "..."}
    - Raises HTTPException on errors.
    """
    logger.info(f"Received request for analysis. Files: {[f.filename for f in files]}, Prompt: '{prompt}'")
    
    # Ensure client is initialized (it might not be if API key was invalid on startup)
    if using_fallback_mode or client is None:
        logger.warning("OpenAI client not available or in fallback mode. Returning fallback response.")
        # Return a specific fallback response structure
        return { 
            "english": "Analysis service is currently unavailable due to configuration issues.",
            "thai": "บริการวิเคราะห์ไม่พร้อมใช้งานในขณะนี้เนื่องจากปัญหาการกำหนดค่า"
        }

    if not files:
        logger.warning("No files provided in the request to analyze_media.")
        raise HTTPException(status_code=400, detail="No media files provided.")

    # Determine input type
    is_video = False
    video_details: Optional[Dict[str, Any]] = None # Explicitly type hint
    image_files: List[UploadFile] = []

    if len(files) == 1 and files[0].content_type and files[0].content_type.startswith('video/'):
        is_video = True
        video_file = files[0]
        logger.info(f"Detected video file: {video_file.filename}")
        
        # Save video file to temporary location to process it
        temp_file_path = None
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{video_file.filename.split('.')[-1]}") as temp_file:
                temp_file_path = temp_file.name
                contents = await video_file.read()
                temp_file.write(contents)
            
            # Extract video metadata
            video_details = {
                "filename": video_file.filename or "unknown_video",
                "mimetype": video_file.content_type,
                "size": video_file.size or 0,
                "duration": "Unknown", 
                "thumbnailBase64": None,
                "file_path": temp_file_path  # Store path for frame extraction
            }
            # Instead of just metadata analysis, extract frames and analyze them
            result = extract_frames_and_analyze_video(video_details, prompt)
        except Exception as e:
            logger.error(f"Error processing video file: {e}")
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise HTTPException(status_code=500, detail=f"Error processing video file: {str(e)}")
        finally:
            # Reset file position for potential future reads
            await video_file.seek(0)
            # Delete temp file when done (if it exists)
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        return result
    elif all(f.content_type and f.content_type.startswith('image/') for f in files):
        logger.info(f"Detected {len(files)} image file(s).")
        image_files = files # Keep the list of UploadFile objects for now
    else:
        # Clean up any opened files before raising error
        for f in files:
            await f.close()
        logger.warning("Invalid file combination. Upload multiple images OR a single video.")
        raise HTTPException(status_code=400, detail="Invalid file combination. Please upload one or more images (JPG, PNG) or a single video (MP4).")

    # --- Call OpenAI --- 
    # Moved the actual API call logic into separate functions below
    try:
        if is_video and video_details:
            result = generate_story_from_video(video_details, prompt)
        elif image_files:
            # Process images (read, encode, close) just before the API call
            base64_images = []
            for img_file in image_files:
                try:
                    contents = await img_file.read()
                    base64_image = base64.b64encode(contents).decode('utf-8')
                    base64_images.append(base64_image)
                finally:
                    await img_file.close() # Ensure file is closed even if encoding fails
            
            if len(base64_images) == 1:
                result = generate_story_from_image(base64_images[0], prompt)
            else:
                result = generate_story_from_multiple_images(base64_images, prompt)
        else:
             # This case should ideally not be reached due to prior validation
             logger.error("Reached unexpected state in analyze_media function.")
             raise HTTPException(status_code=500, detail="Internal server error: Could not determine processing path.")

        logger.info(f"Successfully generated analysis for: {[f.filename for f in files]}")
        return result # Return the dict directly

    except OpenAIError as e: # Catch OpenAI specific errors here
        logger.error(f"OpenAI API error during analysis: {e}")
        detail = f"OpenAI API Error: {e.message}" if hasattr(e, 'message') else str(e)
        status_code = e.status_code if hasattr(e, 'status_code') else 503
        raise HTTPException(status_code=status_code, detail=detail)
    except Exception as e: # Catch other errors during file processing or API call
        logger.exception("An unexpected error occurred during analysis function execution.") # Log traceback
        # Ensure any remaining open files are closed (though they should be closed in the loop)
        for f in files: 
            try:
                await f.close()
            except Exception:
                pass # Ignore errors during cleanup close
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during analysis: {str(e)}")

def extract_frames_and_analyze_video(video_details: Dict[str, Any], user_prompt: str) -> Dict[str, str]:
    """
    Extract frames from video, analyze them and generate a story.
    
    Args:
        video_details: Dictionary containing video details
        user_prompt: Optional user prompt to guide the story generation
        
    Returns:
        Dict with video details, story, and other metadata
    """
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Processing video: {video_details.get('filename')}")
    
    # Extract more detailed metadata using FFmpeg before attempting frame extraction
    try:
        probe = ffmpeg.probe(video_details.get('file_path'))
        # Extract video stream info
        video_stream = next((stream for stream in probe['streams'] 
                            if stream['codec_type'] == 'video'), None)
        
        if video_stream:
            # Update video details with more accurate information
            video_details['width'] = int(video_stream.get('width', 0))
            video_details['height'] = int(video_stream.get('height', 0))
            video_details['frame_rate'] = eval(video_stream.get('r_frame_rate', '0/1'))
            
            # Calculate duration more accurately
            if 'duration' in video_stream:
                duration_sec = float(video_stream['duration'])
                video_details['duration'] = f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}"
                video_details['duration_seconds'] = duration_sec
            
            # Get total frames if available
            if 'nb_frames' in video_stream:
                video_details['total_frames'] = int(video_stream['nb_frames'])
            
        # Check for audio streams
        audio_stream = next((stream for stream in probe['streams'] 
                            if stream['codec_type'] == 'audio'), None)
        video_details['has_audio'] = audio_stream is not None
        if audio_stream:
            video_details['audio_codec'] = audio_stream.get('codec_name', 'unknown')
            
    except Exception as e:
        logger.warning(f"Failed to extract detailed metadata with FFmpeg: {e}")
    
    # Try to extract frames using OpenCV first
    frames = []
    try:
        cap = cv2.VideoCapture(video_details.get('file_path'))
        if not cap.isOpened():
            raise Exception("Failed to open video file with OpenCV")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Update video_details with OpenCV values if we have them
        if fps > 0:
            video_details['frame_rate'] = fps
        if frame_count > 0:
            video_details['total_frames'] = frame_count
        if duration > 0:
            video_details['duration_seconds'] = duration
            video_details['duration'] = f"{int(duration // 60)}:{int(duration % 60):02d}"
        
        # Extract frames - aim for 10 evenly spaced frames
        if frame_count > 0:
            target_frames = min(10, frame_count)
            frame_indices = [int(i * frame_count / target_frames) for i in range(target_frames)]
            
            for frame_idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    # Convert from BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(frame_rgb)
                    
        cap.release()
        logger.info(f"Successfully extracted {len(frames)} frames with OpenCV")
        
    except Exception as e:
        logger.warning(f"Failed to extract frames with OpenCV: {e}")
        
    # If OpenCV failed to extract any frames, try with FFmpeg as fallback
    if not frames:
        logger.info("Falling back to FFmpeg for frame extraction")
        try:
            # Create output directory for frames
            frame_files = []
            
            # Calculate timestamps for 10 evenly distributed frames
            if 'duration_seconds' in video_details and video_details['duration_seconds'] > 0:
                duration_sec = video_details['duration_seconds']
                timestamps = [i * duration_sec / 10 for i in range(10)]
                
                for i, timestamp in enumerate(timestamps):
                    out_file = os.path.join(temp_dir, f"frame_{i:03d}.jpg")
                    ffmpeg.input(video_details.get('file_path'), ss=timestamp).output(
                        out_file, vframes=1, format='image2', vcodec='mjpeg'
                    ).overwrite_output().run(quiet=True, capture_stdout=True, capture_stderr=True)
                    
                    frame_files.append(out_file)
                    
                # Read the extracted frames
                for frame_file in frame_files:
                    if os.path.exists(frame_file) and os.path.getsize(frame_file) > 0:
                        img = cv2.imread(frame_file)
                        if img is not None:
                            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            frames.append(img_rgb)
                
                logger.info(f"Successfully extracted {len(frames)} frames with FFmpeg")
            else:
                logger.warning("Could not determine video duration for FFmpeg frame extraction")
                
        except Exception as e:
            logger.error(f"FFmpeg frame extraction also failed: {e}")
    
    # If we have frames, convert them to base64 and analyze
    frame_images = []
    if frames:
        try:
            for frame in frames:
                # Convert to base64
                success, encoded_img = cv2.imencode('.jpg', cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                if success:
                    img_base64 = base64.b64encode(encoded_img).decode('utf-8')
                    frame_images.append(img_base64)
            
            video_details['frame_count'] = len(frame_images)
            result = analyze_frames(frame_images, video_details, user_prompt)
            
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
            return result
            
        except Exception as e:
            logger.error(f"Error processing frames: {e}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            # Fall through to metadata-only analysis
    
    # If we couldn't extract any frames, generate a story based on metadata only
    logger.warning("No frames could be extracted. Falling back to metadata-only analysis.")
    shutil.rmtree(temp_dir, ignore_errors=True)
    result = video_details.copy()
    story_result = generate_story_from_video(video_details, user_prompt)
    result.update(story_result)
    return result

def analyze_frames(frame_images: List[str], video_details: Dict[str, Any], user_prompt: str) -> Dict[str, str]:
    """
    Analyzes video frames and generates a story based on the content of those frames.
    
    Args:
        frame_images: List of base64-encoded frames from the video
        video_details: Dictionary containing video metadata
        user_prompt: Optional user prompt to guide the story generation
        
    Returns:
        Dict with video details and generated story
    """
    logger.info(f"Analyzing {len(frame_images)} frames from video")
    
    if len(frame_images) == 0:
        raise ValueError("No frames provided for analysis")
    
    try:
        # Reuse the multiple images story generation function as it already handles
        # multiple base64-encoded images, which is what our frames are
        story_result = generate_story_from_multiple_images(frame_images, 
            user_prompt or "Create an engaging caption that captures what's happening in this video")
        
        # Combine video details with the story result
        result = video_details.copy()
        result.update(story_result)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_frames function: {e}")
        # Fall back to metadata-only analysis if frame analysis fails
        fallback_result = generate_story_from_video(video_details, user_prompt)
        result = video_details.copy()
        result.update(fallback_result)
        return result

# --- Specific OpenAI Call Functions ---

# System prompt (as defined in TS example and PRD)
STORY_GENERATION_PROMPT = """
You are a storyteller with the raw, gritty, and unapologetic style of Anthony Bourdain.

Analyze the provided image(s) or video metadata carefully. Describe what you see with:
- Unflinching honesty and sharp observations
- Colorful, sometimes profane language (but not gratuitous)
- Appreciation for the authentic and unglamorous aspects
- Cultural and social context, when relevant
- A touch of world-weary wisdom and dark humor

Return ONLY a JSON object with these fields:
- english: A vivid, Bourdain-esque description (50-75 words) that captures the essence of the visual content
- thai: The description translated to Thai

Your description should feel like it could be narrated in a travel show, with sensory details and thoughtful observations about what's shown.
Never mention AI, this prompt, or formatting in your response.
"""

# Response parsing function (handles potential markdown/JSON issues)
def parse_openai_response(content: Optional[str]) -> Dict[str, str]:
    if not content:
        raise ValueError("No content received from OpenAI")

    try:
        # Attempt to extract JSON from markdown code blocks first
        # More robust regex to handle optional language specifier and whitespace
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if match:
            json_content = match.group(1)
            logger.info("Extracted JSON content from markdown code block.")
        else:
            # If no code block, assume the content might be raw JSON (or need cleaning)
            # Basic cleaning: remove potential leading/trailing ``` if they exist without proper JSON structure
            json_content = content.strip().strip("`")
            if json_content.lower().startswith('json'):
                json_content = json_content[4:].lstrip()

        # Parse the JSON
        parsed_data = json.loads(json_content)
        
        # Validate expected fields (basic validation)
        if not isinstance(parsed_data, dict) or 'english' not in parsed_data:
             raise ValueError("Parsed JSON does not contain the required 'english' field.")
        
        # Ensure english is string, thai is string or None
        english = str(parsed_data.get('english', ''))
        thai = str(parsed_data.get('thai', '')) if parsed_data.get('thai') is not None else None
        
        return {"english": english, "thai": thai or ""} # Return empty string if thai is None/missing

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from OpenAI response: {e}")
        logger.error(f"Raw content: {content[:500]}...") # Log partial raw content
        raise ValueError(f"Could not parse JSON response from AI: {e}")
    except Exception as e:
        logger.error(f"Error processing OpenAI response content: {e}")
        logger.error(f"Raw content: {content[:500]}...")
        raise ValueError(f"Error processing AI response: {e}")

def generate_story_from_image(base64_image: str, user_prompt: str) -> Dict[str, str]:
    """Generates story from a single base64 encoded image using the OpenAI Responses API."""
    logger.info("Generating story from single image (Responses API).")
    if client is None:
        raise RuntimeError("OpenAI client not initialized")

    input_data = [
        {
            "role": "user",
            "content": [
                {"type": "input_text", "text": user_prompt or "Create an engaging caption for this image that captures its essence and tells its story."},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{base64_image}"}
            ]
        }
    ]

    try:
        response = client.responses.create(
            model=active_vision_model,
            input=input_data,
            instructions=STORY_GENERATION_PROMPT
            # max_tokens is not supported in Responses API; control output length via prompt/instructions
        )
        # Prefer the output_text attribute if available (as in SDK example)
        if hasattr(response, "output_text") and response.output_text:
            return parse_openai_response(response.output_text)
        # Otherwise, search for the first output_text block in response.output
        for block in response.output:
            for content in getattr(block, "content", []):
                if getattr(content, "type", None) == "output_text":
                    return parse_openai_response(getattr(content, "text", ""))
        raise ValueError("No output_text found in OpenAI response")
    except Exception as e:
        logger.error(f"Error in generate_story_from_image (Responses API): {e}")
        raise

def generate_story_from_multiple_images(base64_images: List[str], user_prompt: str) -> Dict[str, str]:
    """Generates story from multiple base64 encoded images using the OpenAI Responses API."""
    logger.info(f"Generating story from {len(base64_images)} images (Responses API).")
    if client is None:
        raise RuntimeError("OpenAI client not initialized")

    user_content: List[Dict[str, Any]] = [
        {"type": "input_text", "text": user_prompt or "Create an engaging caption that connects these images and tells their collective story."}
    ]
    for img_b64 in base64_images:
        user_content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{img_b64}"})

    input_data = [
        {"role": "user", "content": user_content}
    ]

    try:
        response = client.responses.create(
            model=active_vision_model,
            input=input_data,
            instructions=STORY_GENERATION_PROMPT
            # max_tokens is not supported in Responses API; control output length via prompt/instructions
        )
        if hasattr(response, "output_text") and response.output_text:
            return parse_openai_response(response.output_text)
        for block in response.output:
            for content in getattr(block, "content", []):
                if getattr(content, "type", None) == "output_text":
                    return parse_openai_response(getattr(content, "text", ""))
        raise ValueError("No output_text found in OpenAI response")
    except Exception as e:
        logger.error(f"Error in generate_story_from_multiple_images (Responses API): {e}")
        raise

def generate_story_from_video(video_details: Dict[str, Any], user_prompt: str) -> Dict[str, str]:
    """
    Generates a story based on video metadata when frame extraction fails.
    Uses available metadata like duration, resolution, filename, etc.
    """
    logger.info("Falling back to metadata-based video analysis")
    
    # Prepare metadata description
    filename = video_details.get('filename', 'Unknown file')
    duration = video_details.get('duration', 'Unknown')
    width = video_details.get('width', 'Unknown')
    height = video_details.get('height', 'Unknown')
    has_audio = video_details.get('has_audio', False)
    audio_codec = video_details.get('audio_codec', 'unknown') if has_audio else 'none'
    
    metadata_description = (
        f"A video file named '{filename}' with duration {duration}. "
        f"Resolution: {width}x{height}. "
    )
    
    if has_audio:
        metadata_description += f"The video has audio using {audio_codec} codec. "
    else:
        metadata_description += "The video does not have audio. "
    
    # Add file extension info for context
    file_ext = os.path.splitext(filename)[1].lower() if filename != 'Unknown file' else ''
    if file_ext:
        metadata_description += f"The video format is {file_ext}. "
    
    if user_prompt:
        metadata_description += f"User prompt: {user_prompt}"
    
    try:
        # Use the Responses API to generate a story based on metadata
        response = client.responses.create(
            model=active_vision_model,
            input=[
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "input_text", 
                            "text": f"Create an engaging caption for a video with these details: {metadata_description}"
                        }
                    ]
                }
            ],
            instructions=STORY_GENERATION_PROMPT
        )
        
        if hasattr(response, "output_text") and response.output_text:
            return parse_openai_response(response.output_text)
        
        for block in response.output:
            for content in getattr(block, "content", []):
                if getattr(content, "type", None) == "output_text":
                    return parse_openai_response(getattr(content, "text", ""))
        
        # If no text is found in response
        return {"story": f"This appears to be a {duration} video named '{filename}'. Without being able to see the content, I cannot provide specific details about what it contains."}
    
    except Exception as e:
        logger.error(f"Error in metadata-based video analysis: {e}")
        return {"story": f"This appears to be a video file named '{filename}'. I wasn't able to analyze its contents."}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    # Use reload=True for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 