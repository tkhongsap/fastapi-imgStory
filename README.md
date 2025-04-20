# FastAPI ImgStroy

A media analysis application that generates creative stories from images and videos using OpenAI's vision models.

## Project Overview

FastAPI ImgStroy is a web application that analyzes uploaded media (images or videos) and generates descriptive stories in both English and Thai languages. The application uses OpenAI's GPT-4 Vision to analyze visual content and create engaging stories in the style of Anthony Bourdain.

## Features

- Upload and analyze images (JPG, PNG) or videos (MP4)
- Support for single or multiple image analysis
- Video frame extraction and analysis
- Optional text prompts to guide story generation
- Dual language output (English and Thai)
- Token usage tracking
- Web interface for easy interaction
- Detailed API documentation

## Prerequisites

- Python 3.8+
- OpenAI API key
- FFmpeg (for video processing)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/fastapi-imgStroy.git
   cd fastapi-imgStroy
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install FFmpeg (required for video processing):
   - **Windows**: Download from [FFmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key
   # OPENAI_ORG_ID=your_org_id  # Optional: Uncomment if using organization ID
   ```

## Usage

1. Start the server:
   ```
   python main.py
   ```
   Alternatively, you can use:
   ```
   uvicorn main:app --reload
   ```
   
   For Windows users, you can use the provided PowerShell script:
   ```
   .\restart-server.ps1
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

3. Upload media files and optionally provide a prompt to guide the story generation.

4. View the detailed API documentation at:
   ```
   http://localhost:8000/api/docs
   ```

## API Endpoints

The application provides the following endpoints:

### GET /

Serves the web interface for interacting with the application.

### GET /api/docs

Serves the API documentation with detailed endpoint information, request parameters, and example responses.

### POST /analyze/

Processes uploaded media files and generates creative stories.

**Request:**
- **Method**: POST
- **Content-Type**: multipart/form-data
- **Parameters**:
  - `files`: Media files to analyze (JPG, PNG images or MP4 video)
  - `prompt` (optional): Text to guide the story generation

**Example Request (using curl):**
```bash
curl -X POST http://localhost:8000/analyze/ \
  -F "files=@/path/to/your/image.jpg" \
  -F "prompt=Generate a story about this image in the style of Anthony Bourdain"
```

**Response:**
```json
{
  "english": "English language story generated from the media",
  "thai": "Thai language translation of the story",
  "token_usage": {
    "input_tokens": 123,
    "output_tokens": 456,
    "total_tokens": 579
  }
}
```

**Error Responses:**

| Status Code | Description |
|-------------|-------------|
| 400 | Bad Request - Invalid file type, file size exceeds limits, or other client errors |
| 422 | Unprocessable Entity - The server understands the content type but was unable to process the contained instructions |
| 429 | Too Many Requests - Rate limit exceeded with the OpenAI API |
| 500 | Internal Server Error - Something went wrong on the server side |
| 503 | Service Unavailable - The OpenAI API is temporarily unavailable |

## Project Structure

```
fastapi-imgStroy/
├── .env                  # Environment variables
├── main.py               # FastAPI application entry point
├── requirements.txt      # Python dependencies
├── restart-server.ps1    # Server restart script for Windows
├── TASKS.md              # Project tasks and progress tracking
├── static/               # Static files (HTML, CSS, JavaScript)
│   ├── index.html        # Web interface
│   ├── script.js         # Frontend JavaScript
│   └── style.css         # CSS styles
├── uploads/              # Directory for media uploads
└── utils/                # Utility modules
    ├── __init__.py       # Package initialization
    ├── media_analysis.py # Media processing functions
    ├── openai_client.py  # OpenAI API client
    ├── prompts.py        # Prompt templates
    └── story_generation.py # Story generation functions
```

## Environment Variables

The application uses the following environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| OPENAI_API_KEY | Yes | Your OpenAI API key for accessing the API |
| OPENAI_ORG_ID | No | Optional: Your OpenAI organization ID if you're using one |

## Troubleshooting

### Common Issues

1. **"OpenAI API key not found" error**
   - Make sure your `.env` file is in the project root directory
   - Check that the OPENAI_API_KEY variable is set correctly
   - Restart the server after making changes to the `.env` file

2. **FFmpeg related errors**
   - Ensure FFmpeg is installed and accessible in your PATH
   - Try running `ffmpeg -version` in your terminal to verify the installation

3. **File upload issues**
   - Check that your files are of the supported types (JPG, PNG, MP4)
   - Ensure that image files are under 10MB and video files are under 50MB

## Future Improvements

- Enhanced video processing with audio track analysis
- Improved thumbnail generation for videos
- Performance optimizations and caching
- Support for additional media formats
- Advanced prompt customization

## License

[MIT License](LICENSE) 