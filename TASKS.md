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

## In Progress Tasks
- [ ] Implement FastAPI backend (`main.py`)
    - [ ] Load environment variables (`python-dotenv`)
    - [ ] Initialize FastAPI app and CORS
    - [ ] Implement OpenAI client setup and API key validation
    - [ ] Define API endpoint (`/analyze/`) to accept file uploads and optional prompt (using `Form`)
    - [ ] Implement logic to identify input type (single image, multiple images, video)
    - [ ] Implement Base64 encoding for images
    - [ ] Implement function to call OpenAI for single/multiple images (translate `generateStoryFromImage`/`generateStoryFromMultipleImages`)
    - [ ] Implement basic video handling (save temp file, get metadata - filename, size, type)
    - [ ] Implement function to call OpenAI for video metadata (translate `generateStoryFromVideo` - without thumbnail for PoC)
    - [ ] Integrate optional text prompt into OpenAI calls
    - [ ] Implement response parsing and JSON formatting (`{"english": "...", "thai": "..."}`)
    - [ ] Add error handling for API calls and file processing
    - [ ] Add root endpoint (`/`) to serve the `index.html` file
    - [ ] Mount the `static` directory

## Upcoming Tasks
- [ ] Test backend endpoints thoroughly (single image, multiple images, video, prompt variations)
- [ ] Test frontend interaction and display (loading, results, errors)
- [ ] Refine error handling and messages (frontend and backend)
- [ ] Add basic logging to the backend
- [ ] Consider adding simple validation for file types/sizes on the backend
- [ ] (Optional/Future) Explore adding thumbnail generation for videos if time permits and complexity is manageable within PoC scope.
- [ ] Prepare instructions for running the application (`README.md`) 