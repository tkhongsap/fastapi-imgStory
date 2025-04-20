Product Requirements Document: Media Analysis Story Generator Prototype
Version: 1.0
Date: April 19, 2025
Author: [Your Name/Team Name]
________________________________________
1. Introduction
This document outlines the requirements for a simple web application prototype designed to showcase the capability of generating social media captions ("stories") from uploaded image and video files using AI vision models (specifically OpenAI Vision).
The primary goal of this prototype is to serve as a proof-of-concept (PoC) and a tangible demonstration for team discussion regarding the technical feasibility, user flow, and potential application design before committing to a full-scale development effort.
2. Goals and Objectives
•	Primary: Validate the technical feasibility of using OpenAI Vision API to analyze visual media (images, potentially basic video) and generate relevant textual outputs (social media captions).
•	Primary: Demonstrate a basic end-to-end user flow: User uploads media -> System processes -> User sees generated caption.
•	Secondary: Gather feedback from the team on the concept, the quality of AI-generated content, and potential future features.
•	Secondary: Provide a foundation for discussing the architecture and design of a potential future production application.
3. User Stories
•	As a user, I want to upload a single image file so that I can receive an AI-generated social media caption for it.
•	As a user, I want to upload multiple image files so that I can receive an AI-generated social media caption that attempts to tell a story across the images.
•	As a user, I want to upload a video file so that I can receive an AI-generated social media caption based on its metadata and potentially a thumbnail. (Note: Full video frame analysis is out of scope for this phase).
•	As a user, I want to optionally provide a short text prompt to influence the generated caption.
•	As a user, I want to see the generated social media caption displayed clearly on the page in both English and Thai.
•	As a user, I want to see a simple indicator or message while the analysis is in progress.
•	As a user, I want to be notified if an error occurs during the analysis process.
4. Scope (In/Out)
4.1. In Scope for Prototype:
•	Basic web interface (HTML/JavaScript) for file upload and results display.
•	Backend API built with FastAPI (Python) to receive files and interact with OpenAI.
•	Ability to upload one or more image files (e.g., JPG, PNG).
•	Ability to upload a single video file (e.g., MP4).
•	Backend processing to convert uploaded images to Base64 for OpenAI Vision API.
•	Backend processing to handle multiple image inputs for a single OpenAI call.
•	Backend processing for videos limited to using metadata (filename, size, duration if available) and potentially extracting/using a single thumbnail image.
•	Integration with the OpenAI Chat Completions API (gpt-4-turbo, gpt-4o or similar vision models).
•	Sending a predefined system prompt (translated from STORY_GENERATION_PROMPT) and user content (text prompt + media data) to OpenAI.
•	Receiving and parsing the JSON response from OpenAI (including handling markdown code blocks).
•	Displaying the generated English and Thai captions on the frontend.
•	Basic loading state indication on the frontend.
•	Basic error message display on the frontend for API or parsing failures.
•	Loading OpenAI API key securely via environment variables on the backend.
4.2. Out of Scope for Prototype:
•	User authentication or accounts.
•	Saving uploaded media or generated captions.
•	Advanced video processing (e.g., extracting multiple frames, analyzing frame sequences for narrative, generating transcriptions).
•	Any form of content moderation or safety filtering beyond what the OpenAI API might provide by default.
•	Complex UI/UX features (e.g., drag-and-drop uploads, progress bars, rich text editing).
•	Comprehensive support for all possible image or video file types and codecs.
•	Optimized handling of very large files.
•	Production-level error handling, logging, monitoring, and scalability.
•	Integration with social media posting APIs.
•	Internationalization (i18n) beyond the English/Thai output from the AI.
•	Advanced styling or branding beyond basic HTML.
5. Features
•	File Upload Interface: A simple web page with a file input element (<input type="file">) allowing selection of one or multiple image files, or a single video file. Supported formats will include common image types (JPG, PNG) and video types (MP4).
•	Optional Prompt Input: An optional text field where the user can enter a short custom instruction or detail to include in the prompt sent to the AI.
•	Analyze Button: A button that, when clicked, triggers the upload of selected files and the optional prompt to the backend API.
•	Loading Indicator: A simple text message or spinner displayed while the backend is processing the request and waiting for the AI response.
•	Results Display Area: Dedicated sections on the page to display the generated English and Thai captions received from the backend.
•	Error Messages: If the backend returns an error (e.g., API key issue, parsing failure, OpenAI error), a clear message will be displayed to the user.
6. Technical Considerations
•	Backend Framework: FastAPI (Python).
•	OpenAI Integration: Python openai library.
•	File Handling: Using UploadFile and File in FastAPI, potentially python-multipart for form data parsing.
•	Image Processing: Basic image reading and Base64 encoding (e.g., using built-in Python libraries or Pillow if necessary).
•	Video Handling (Limited): Saving video files temporarily, extracting basic metadata. Thumbnail extraction might require a library or subprocess calls to FFmpeg (assess complexity vs. prototype goals).
•	Frontend Technologies: HTML, vanilla JavaScript (Fetch API for AJAX requests, FormData for file uploads). Basic CSS for layout is acceptable.
•	API Keys: OpenAI API key must be stored securely on the backend using environment variables (python-dotenv).
•	CORS: CORS middleware will be required in FastAPI to allow the frontend (likely on a different port) to communicate with the backend.
•	OpenAI Model: The prototype will primarily target vision-capable models like gpt-4o or gpt-4-turbo. Model selection logic may be included based on input type (e.g., prefer gpt-4o for multi-image).
•	Response Format: Backend will return a JSON object { "english": "...", "thai": "..." }. Frontend will parse this JSON.
7. Future Considerations (Beyond Prototype)
•	Implementing robust video analysis pipelines (FFmpeg integration for frames, audio transcription APIs).
•	Adding support for more diverse media formats and inputs.
•	Developing a more sophisticated and user-friendly interface (e.g., drag-and-drop, visual feedback during upload/processing).
•	Adding features to edit, save, or share generated captions.
•	Implementing user accounts and history.
•	Exploring different AI models or prompting strategies.
•	Developing a production-ready deployment strategy with scalability and monitoring.
•	Implementing comprehensive error handling and logging.
8. Success Metrics
The prototype will be considered successful if:
•	It can successfully process image uploads and generate coherent captions via the OpenAI API.
•	It can successfully process basic video uploads (metadata/thumbnail) and generate a caption based on that information.
•	The team can successfully use the prototype to understand the core concept and initiate discussions about the full application design and technical approach.
•	The code provides a clear starting point for potential future development, particularly the translated Python OpenAI logic.