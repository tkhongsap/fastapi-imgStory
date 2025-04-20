"""
Story Generation Utility Module

This module handles the generation of stories from various media types
(single image, multiple images, video) using OpenAI's vision model.
"""

import json
import re
import logging
from typing import List, Dict, Optional, Any

# Import from our utilities
from utils import openai_client

# Configure logging
logger = logging.getLogger(__name__)

# Constants
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

def parse_openai_response(content: Optional[str]) -> Dict[str, str]:
    """
    Parse the response from OpenAI, extracting and validating the JSON.
    
    Args:
        content: The raw response content from OpenAI
        
    Returns:
        Dict with parsed content, containing 'english' and 'thai' fields
        
    Raises:
        ValueError: If the response can't be parsed or is missing required fields
    """
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
    """
    Generates story from a single base64 encoded image using the OpenAI Responses API.
    
    Args:
        base64_image: The base64-encoded image data
        user_prompt: Optional user prompt to guide the story generation
        
    Returns:
        Dict with 'english' and 'thai' fields
        
    Raises:
        RuntimeError: If OpenAI client is not initialized
        ValueError: If response parsing fails
    """
    logger.info("Generating story from single image (Responses API).")
    if openai_client.get_client() is None:
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
        response = openai_client.get_client().responses.create(
            model=openai_client.get_active_model(),
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
    """
    Generates story from multiple base64 encoded images using the OpenAI Responses API.
    
    Args:
        base64_images: List of base64-encoded image data
        user_prompt: Optional user prompt to guide the story generation
        
    Returns:
        Dict with 'english' and 'thai' fields
        
    Raises:
        RuntimeError: If OpenAI client is not initialized
        ValueError: If response parsing fails
    """
    logger.info(f"Generating story from {len(base64_images)} images (Responses API).")
    if openai_client.get_client() is None:
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
        response = openai_client.get_client().responses.create(
            model=openai_client.get_active_model(),
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
    
    Args:
        video_details: Dictionary containing video metadata
        user_prompt: Optional user prompt to guide the story generation
        
    Returns:
        Dict with 'english' and 'thai' fields (or fallback story)
    """
    import os  # Import here to avoid circular imports
    
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
        response = openai_client.get_client().responses.create(
            model=openai_client.get_active_model(),
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
        return {"english": f"This appears to be a {duration} video named '{filename}'. Without being able to see the content, I cannot provide specific details about what it contains.", 
                "thai": ""}
    
    except Exception as e:
        logger.error(f"Error in metadata-based video analysis: {e}")
        return {"english": f"This appears to be a video file named '{filename}'. I wasn't able to analyze its contents.", 
                "thai": ""} 