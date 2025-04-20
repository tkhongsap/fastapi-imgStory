import os
import base64
import json
import re
import logging
import aiofiles
import pathlib # Import pathlib
from typing import List, Dict, Optional, Any

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
# Use gpt-4o-mini as requested in custom instructions
VISION_MODEL = "gpt-4o-mini" 
FALLBACK_VISION_MODEL = "gpt-4o-mini" # Fallback if preferred is unavailable, but mini should be available
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
        # Basic video handling (save metadata)
        # Note: Thumbnail extraction is out of scope for this PoC as per PRD
        video_details = {
            "filename": video_file.filename or "unknown_video",
            "mimetype": video_file.content_type,
            "size": video_file.size or 0, # Get size if available
            # Duration would require a library like moviepy or ffprobe - skipping for PoC
            "duration": "Unknown", 
            "thumbnailBase64": None # No thumbnail extraction
        }
        # Close the file handle for the video file after reading metadata if needed
        # await video_file.close() # Uncomment if you read the file content

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

# --- Specific OpenAI Call Functions ---

# System prompt (as defined in TS example and PRD)
STORY_GENERATION_PROMPT = """
You are an expert social media storyteller for TikTok or Twitter who creates engaging captions from visual content.

Analyze the provided image(s) or video metadata carefully. Pay attention to:
- The scene, setting, and subjects
- Emotions, mood, and atmosphere
- Actions, interactions, and movement
- Colors, lighting, and visual elements
- Cultural or contextual elements

Return ONLY a JSON object with these fields:
- english: A vivid, engaging caption (50-75 words) that captures the essence of the visual content
- thai: The caption translated to Thai

Your caption should use sensory language, convey emotion, hint at a broader story, and be suitable for social media.
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
    """Generates story from a single base64 encoded image."""
    logger.info("Generating story from single image.")
    if client is None: raise RuntimeError("OpenAI client not initialized") # Should be caught earlier

    messages = [
        {"role": "system", "content": STORY_GENERATION_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt or "Create an engaging caption for this image that captures its essence and tells its story."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
        }
    ]

    try:
        # Note: removed 'await' - OpenAI Python client is synchronous
        response = client.chat.completions.create(
            model=active_vision_model,
            messages=messages,
            max_tokens=300, # Reduced max_tokens for caption generation
            # response_format={"type": "json_object"} # Request JSON mode if model supports it reliably
        )
        content = response.choices[0].message.content
        return parse_openai_response(content)
    except Exception as e:
        logger.error(f"Error in generate_story_from_image: {e}")
        raise # Re-raise to be caught by the main endpoint handler

def generate_story_from_multiple_images(base64_images: List[str], user_prompt: str) -> Dict[str, str]:
    """Generates story from multiple base64 encoded images."""
    logger.info(f"Generating story from {len(base64_images)} images.")
    if client is None: raise RuntimeError("OpenAI client not initialized")

    user_content: List[Dict[str, Any]] = [
        {"type": "text", "text": user_prompt or "Create an engaging caption that connects these images and tells their collective story."}
    ]
    for img_b64 in base64_images:
        user_content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}})

    messages = [
        {"role": "system", "content": STORY_GENERATION_PROMPT},
        {"role": "user", "content": user_content}
    ]

    try:
        # Note: removed 'await' - OpenAI Python client is synchronous
        response = client.chat.completions.create(
            model=active_vision_model,
            messages=messages,
            max_tokens=300,
            # response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return parse_openai_response(content)
    except Exception as e:
        logger.error(f"Error in generate_story_from_multiple_images: {e}")
        raise

def generate_story_from_video(video_details: Dict[str, Any], user_prompt: str) -> Dict[str, str]:
    """Generates story from video metadata (no visual content as per PoC)."""
    logger.info(f"Generating story from video metadata: {video_details.get('filename')}")
    if client is None: raise RuntimeError("OpenAI client not initialized")

    # Construct a text prompt based on metadata
    metadata_text = f"Analyze the metadata for a video:\n"
    metadata_text += f"- Filename: {video_details.get('filename', 'N/A')}\n"
    metadata_text += f"- Duration: {video_details.get('duration', 'Unknown')}\n"
    metadata_text += f"- Format: {video_details.get('mimetype', 'N/A')}\n"
    metadata_text += f"- Size: {round(video_details.get('size', 0) / (1024*1024), 1)}MB\n"
    metadata_text += f"\n{user_prompt or 'Create an engaging social media caption based on this video metadata.'}"

    messages = [
        {"role": "system", "content": STORY_GENERATION_PROMPT},
        {"role": "user", "content": [{"type": "text", "text": metadata_text}]}
        # No image_url for video metadata-only analysis
    ]

    try:
        # Note: removed 'await' - OpenAI Python client is synchronous
        response = client.chat.completions.create(
            model=active_vision_model, # Vision model can handle text-only input
            messages=messages,
            max_tokens=300,
            # response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return parse_openai_response(content)
    except Exception as e:
        logger.error(f"Error in generate_story_from_video: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    # Use reload=True for development
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 