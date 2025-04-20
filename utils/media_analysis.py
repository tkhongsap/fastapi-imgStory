"""
Media Analysis Utility Module

This module handles the analysis of media files (images and videos) using OpenAI's vision model.
"""

import os
import base64
import tempfile
import cv2
import ffmpeg
import shutil
import logging
from typing import List, Dict, Optional, Any
from fastapi import HTTPException, UploadFile
from openai import OpenAIError

# Import from our utilities
from utils import openai_client
from utils.prompts import STORY_GENERATION_PROMPT
from utils.story_generation import (
    generate_story_from_image,
    generate_story_from_multiple_images,
    generate_story_from_video
)

# Configure logging
logger = logging.getLogger(__name__)

# Constants
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png']
ALLOWED_VIDEO_TYPES = ['video/mp4']
MAX_IMAGE_SIZE_MB = 10  # 10MB max per image
MAX_VIDEO_SIZE_MB = 50  # 50MB max for video
MB = 1024 * 1024  # 1MB in bytes

async def validate_files(files: List[UploadFile]) -> None:
    """
    Validates the uploaded files for type and size.
    
    Args:
        files: List of uploaded files
        
    Raises:
        HTTPException: If validation fails
    """
    if not files:
        raise HTTPException(status_code=400, detail="No media files provided.")
    
    # Check if we have a single video or multiple images
    if len(files) == 1 and files[0].content_type in ALLOWED_VIDEO_TYPES:
        # Video file validation
        video = files[0]
        if video.size and video.size > MAX_VIDEO_SIZE_MB * MB:
            raise HTTPException(
                status_code=413, 
                detail=f"Video file too large. Maximum size allowed is {MAX_VIDEO_SIZE_MB}MB."
            )
    elif all(f.content_type in ALLOWED_IMAGE_TYPES for f in files):
        # Image files validation
        for img in files:
            if img.size and img.size > MAX_IMAGE_SIZE_MB * MB:
                raise HTTPException(
                    status_code=413, 
                    detail=f"Image file '{img.filename}' too large. Maximum size allowed is {MAX_IMAGE_SIZE_MB}MB."
                )
    else:
        # Invalid file types
        invalid_files = [f.filename for f in files if (
            f.content_type not in ALLOWED_IMAGE_TYPES and 
            f.content_type not in ALLOWED_VIDEO_TYPES
        )]
        if invalid_files:
            raise HTTPException(
                status_code=415, 
                detail=f"Unsupported file type(s): {', '.join(invalid_files)}. Only JPG, PNG images and MP4 videos are supported."
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail="Invalid file combination. Please upload one or more images (JPG, PNG) or a single video (MP4)."
            )

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
    
    # Validate the uploaded files
    await validate_files(files)
    
    # Ensure client is initialized or try to reinitialize if needed
    if openai_client.is_fallback_mode() or openai_client.get_client() is None:
        # Try to reinitialize the client one more time
        if not openai_client.reinitialize_client_if_needed():
            logger.warning("OpenAI client still not available or in fallback mode. Returning fallback response.")
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
        
        # Log the token usage for debugging
        logger.info(f"Token usage for frame analysis - Input: {story_result.get('input_tokens', 0)}, "
                    f"Output: {story_result.get('output_tokens', 0)}")
        
        # Combine video details with the story result
        result = video_details.copy()
        result.update(story_result)
        return result
    except Exception as e:
        logger.error(f"Error in analyze_frames function: {e}")
        # Fall back to metadata-only analysis if frame analysis fails
        fallback_result = generate_story_from_video(video_details, user_prompt)
        
        # Log the fallback token usage for debugging
        logger.info(f"Fallback token usage - Input: {fallback_result.get('input_tokens', 0)}, "
                    f"Output: {fallback_result.get('output_tokens', 0)}")
        
        result = video_details.copy()
        result.update(fallback_result)
        return result 