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

## Prerequisites

- Python 3.8+
- OpenAI API key

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

3. Create a `.env` file in the project root with your OpenAI API key:
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

## API Endpoints

- `GET /`: Serves the web interface
- `POST /analyze/`: Processes uploaded media files

### POST /analyze/

**Request:**
- `files`: List of files (JPG, PNG, MP4)
- `prompt` (optional): Text to guide the story generation

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

## Future Improvements

- Enhanced video processing with audio track analysis
- Improved thumbnail generation for videos
- Performance optimizations and caching
- Support for additional media formats
- Advanced prompt customization

## License

[MIT License](LICENSE) 