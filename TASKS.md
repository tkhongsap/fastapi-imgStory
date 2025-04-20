# Media Analysis Story Generator Prototype - Tasks

Based on the PRD (Product Requirements Document) for the PoC.

## Completed Tasks
- [x] Initialize project structure (directories, `.gitignore`)
- [x] Set up `requirements.txt`
- [x] Create `.env` placeholder
- [x] Create basic HTML structure (`static/index.html`)
- [x] Implement basic frontend JavaScript (`static/script.js`) for form handling and API call
- [x] Add basic CSS (`static/style.css`)
- [x] Create initial `TASKS.md`
- [x] Implement FastAPI backend (`main.py`)
    - [x] Load environment variables (`python-dotenv`)
    - [x] Initialize FastAPI app and CORS
    - [x] Implement OpenAI client setup and API key validation
    - [x] Define API endpoint (`/analyze/`) to accept file uploads and optional prompt (using `Form`)
    - [x] Implement logic to identify input type (single image, multiple images, video)
    - [x] Implement Base64 encoding for images
    - [x] Implement function to call OpenAI for single/multiple images (translate `generateStoryFromImage`/`generateStoryFromMultipleImages`)
    - [x] Implement basic video handling (save temp file, get metadata - filename, size, type)
    - [x] Implement function to call OpenAI for video metadata (translate `generateStoryFromVideo` - without thumbnail for PoC)
    - [x] Integrate optional text prompt into OpenAI calls
    - [x] Implement response parsing and JSON formatting (`{"english": "...", "thai": "..."}`)
    - [x] Add error handling for API calls and file processing
    - [x] Add root endpoint (`/`) to serve the `index.html` file
    - [x] Mount the `static` directory
- [x] Add token usage tracking and display
    - [x] Update backend to capture input and output token counts from OpenAI API
    - [x] Update response structure to include token information
    - [x] Add UI elements to display token usage information
    - [x] Style token usage display section

## In Progress Tasks
- [ ] Test backend endpoints thoroughly (single image, multiple images, video, prompt variations)
- [ ] Test frontend interaction and display (loading, results, errors)
- [ ] Refine error handling and messages (frontend and backend)
- [ ] Add basic logging to the backend

## Upcoming Tasks
- [ ] Consider adding simple validation for file types/sizes on the backend
- [ ] (Optional/Future) Explore adding thumbnail generation for videos if time permits and complexity is manageable within PoC scope.
- [ ] Prepare instructions for running the application (`README.md`) 