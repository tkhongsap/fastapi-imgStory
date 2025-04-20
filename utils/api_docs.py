"""
API documentation utilities for the FastAPI ImgStroy application.
This module contains functions for generating API documentation in HTML format.
"""

def generate_api_docs_html():
    """
    Generate basic API documentation HTML if the api_docs.html file isn't found.
    Returns a complete HTML page with documentation for all API endpoints.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ImgStory API - Documentation</title>
        <link rel="stylesheet" href="/static/style.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --sidebar-width: 260px;
                --header-height: 60px;
                --code-bg: #f8f9fa;
                --code-border: #e9ecef;
                --method-get: #61affe;
                --method-post: #49cc90;
                --method-put: #fca130;
                --method-delete: #f93e3e;
                --method-patch: #50e3c2;
                --method-options: #0d5aa7;
                --heading-color: #3b4151;
                --text-color: #4a4a4a;
                --border-color: #eaeaea;
                --sidebar-bg: #fafafa;
                --sidebar-item-hover: #f0f0f0;
                --sidebar-active: #e8f4fd;
                --sidebar-border: #efefef;
            }

            body {
                display: flex;
                flex-direction: column;
                min-height: 100vh;
                margin: 0;
                padding: 0;
                color: var(--text-color);
            }

            .top-header {
                height: var(--header-height);
                background-color: #fff;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 20px;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 1000;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }

            .top-header .brand {
                display: flex;
                align-items: center;
                font-weight: 600;
            }

            .top-header .brand i {
                margin-right: 10px;
                color: var(--primary-color);
            }

            .top-header .nav-menu {
                display: flex;
                align-items: center;
                gap: 20px;
            }

            .top-header .nav-menu a {
                color: var(--text-color);
                text-decoration: none;
                font-weight: 500;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .top-header .nav-menu a:hover {
                color: var(--primary-color);
            }

            .api-version {
                background-color: var(--primary-color);
                color: white;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 0.75rem;
                font-weight: 600;
            }

            .content-wrapper {
                display: flex;
                margin-top: var(--header-height);
                flex: 1;
            }

            .sidebar {
                width: var(--sidebar-width);
                background-color: var(--sidebar-bg);
                border-right: 1px solid var(--sidebar-border);
                overflow-y: auto;
                position: fixed;
                top: var(--header-height);
                bottom: 0;
                padding: 20px 0;
            }

            .sidebar-section {
                margin-bottom: 20px;
            }

            .sidebar-section h3 {
                font-size: 0.9rem;
                text-transform: uppercase;
                color: #999;
                padding: 0 20px;
                margin: 15px 0 10px;
            }

            .sidebar-item {
                padding: 10px 20px;
                display: flex;
                align-items: center;
                gap: 8px;
                cursor: pointer;
                transition: background-color 0.2s ease;
            }

            .sidebar-item:hover {
                background-color: var(--sidebar-item-hover);
            }

            .sidebar-item.active {
                background-color: var(--sidebar-active);
                border-left: 3px solid var(--primary-color);
                font-weight: 500;
            }

            .sidebar-item .method {
                font-size: 0.75rem;
                padding: 2px 6px;
                border-radius: 3px;
                color: white;
                min-width: 40px;
                text-align: center;
            }

            .sidebar-item .method.get {
                background-color: var(--method-get);
            }

            .sidebar-item .method.post {
                background-color: var(--method-post);
            }

            .main-content {
                flex: 1;
                margin-left: var(--sidebar-width);
                padding: 30px;
            }

            .section {
                margin-bottom: 40px;
                max-width: 950px;
            }

            .section h1 {
                color: var(--heading-color);
                font-size: 2.2rem;
                margin-bottom: 20px;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 10px;
            }

            .section h2 {
                color: var(--heading-color);
                font-size: 1.6rem;
                margin: 25px 0 15px;
                padding-top: 15px;
                border-top: 1px solid var(--border-color);
            }

            .section h3 {
                color: var(--heading-color);
                font-size: 1.3rem;
                margin: 20px 0 10px;
            }

            .section p {
                line-height: 1.6;
                margin-bottom: 15px;
            }

            .endpoint {
                margin-bottom: 30px;
                background-color: white;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                overflow: hidden;
            }

            .endpoint-header {
                padding: 15px 20px;
                border-bottom: 1px solid var(--border-color);
                background-color: #fafafa;
            }

            .endpoint-title {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 5px;
            }

            .endpoint-title .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 5px;
                font-weight: 600;
                font-size: 0.8rem;
                text-transform: uppercase;
                color: white;
            }

            .endpoint-title .path {
                font-family: 'Courier New', monospace;
                font-weight: 500;
                color: var(--heading-color);
            }

            .endpoint-body {
                padding: 20px;
            }

            .method.get { background-color: var(--method-get); }
            .method.post { background-color: var(--method-post); }
            .method.put { background-color: var(--method-put); }
            .method.delete { background-color: var(--method-delete); }
            .method.patch { background-color: var(--method-patch); }

            table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0 25px;
                font-size: 0.95rem;
            }

            th, td {
                padding: 10px 15px;
                text-align: left;
                border: 1px solid var(--border-color);
            }

            th {
                background-color: var(--sidebar-bg);
                font-weight: 600;
                color: var(--heading-color);
            }

            tr:nth-child(even) {
                background-color: var(--sidebar-bg);
            }

            pre {
                background-color: var(--code-bg);
                border: 1px solid var(--code-border);
                border-radius: 4px;
                padding: 15px;
                overflow-x: auto;
                margin: 15px 0;
            }

            code {
                font-family: 'Courier New', monospace;
                font-size: 0.9rem;
            }

            .tab-container {
                margin: 20px 0;
            }

            .tab-header {
                display: flex;
                border-bottom: 1px solid var(--border-color);
            }

            .tab {
                padding: 10px 20px;
                cursor: pointer;
                border: 1px solid transparent;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                background-color: #f5f5f5;
                margin-right: 5px;
            }

            .tab.active {
                background-color: white;
                border-color: var(--border-color);
                position: relative;
            }

            .tab.active::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                right: 0;
                height: 1px;
                background-color: white;
            }

            .tab-content {
                display: none;
                padding: 20px;
                border: 1px solid var(--border-color);
                border-top: none;
                background-color: white;
            }

            .tab-content.active {
                display: block;
            }

            .notes-box {
                background-color: #fff8e6;
                border-left: 4px solid #ffb100;
                padding: 15px;
                border-radius: 4px;
                margin: 20px 0;
            }

            .notes-box h4 {
                color: #d18700;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .status-code {
                font-weight: 600;
                margin-right: 10px;
            }

            .status-200 { color: var(--method-post); }
            .status-400 { color: var(--method-delete); }
            .status-401 { color: var(--method-delete); }
            .status-403 { color: var(--method-delete); }
            .status-404 { color: var(--method-delete); }
            .status-429 { color: var(--method-patch); }
            .status-500 { color: var(--method-delete); }
            .status-503 { color: var(--method-delete); }

            @media (max-width: 992px) {
                .sidebar {
                    display: none;
                }
                .main-content {
                    margin-left: 0;
                }
            }

            .try-it-btn {
                background-color: var(--primary-color);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-top: 10px;
            }

            .try-it-btn:hover {
                opacity: 0.9;
            }

            footer {
                background-color: #fff;
                border-top: 1px solid var(--border-color);
                padding: 20px;
                text-align: center;
                font-size: 0.9rem;
                color: #666;
            }
        </style>
    </head>
    <body>
        <header class="top-header">
            <div class="brand">
                <i class="fas fa-cloud"></i>
                ImgStory API
                <span class="api-version">v1.0</span>
            </div>
            <div class="nav-menu">
                <a href="/"><i class="fas fa-home"></i> Home</a>
                <a href="/docs"><i class="fas fa-code"></i> OpenAPI/Swagger</a>
                <a href="https://github.com/tkhongsap/fastapi-imgStory" target="_blank"><i class="fab fa-github"></i> GitHub</a>
            </div>
        </header>

        <div class="content-wrapper">
            <aside class="sidebar">
                <div class="sidebar-section">
                    <h3>Introduction</h3>
                    <div class="sidebar-item active" onclick="scrollToSection('introduction')">
                        <i class="fas fa-book"></i> Overview
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('authentication')">
                        <i class="fas fa-lock"></i> Authentication
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('rate-limits')">
                        <i class="fas fa-tachometer-alt"></i> Rate Limits
                    </div>
                </div>

                <div class="sidebar-section">
                    <h3>Endpoints</h3>
                    <div class="sidebar-item" onclick="scrollToSection('endpoint-home')">
                        <span class="method get">GET</span> /
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('endpoint-docs')">
                        <span class="method get">GET</span> /api/docs
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('endpoint-analyze')">
                        <span class="method post">POST</span> /analyze
                    </div>
                </div>

                <div class="sidebar-section">
                    <h3>Resources</h3>
                    <div class="sidebar-item" onclick="scrollToSection('error-handling')">
                        <i class="fas fa-exclamation-triangle"></i> Error Handling
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('usage-examples')">
                        <i class="fas fa-code"></i> Code Examples
                    </div>
                    <div class="sidebar-item" onclick="scrollToSection('troubleshooting')">
                        <i class="fas fa-bug"></i> Troubleshooting
                    </div>
                </div>
            </aside>

            <main class="main-content">
                <section id="introduction" class="section">
                    <h1>ImgStory API Documentation</h1>
                    <p>Welcome to the ImgStory API documentation. This API allows you to analyze media files (images and videos) 
                    and generate creative stories based on visual content using OpenAI's vision models.</p>
                    
                    <div class="notes-box">
                        <h4><i class="fas fa-lightbulb"></i> Quick Start</h4>
                        <p>The easiest way to get started is to use our web interface at <a href="/">the homepage</a>. 
                        For direct API access, see the endpoint documentation below.</p>
                    </div>

                    <h3>Base URL</h3>
                    <pre><code>http://localhost:8000</code></pre>
                    
                    <p>For production environments, replace with your actual domain.</p>
                </section>

                <section id="authentication" class="section">
                    <h2>Authentication</h2>
                    <p>Currently, the ImgStory API does not require authentication for local usage. 
                    If deploying to production, you may want to implement authentication using API keys 
                    or OAuth2 to secure your endpoints.</p>
                </section>

                <section id="rate-limits" class="section">
                    <h2>Rate Limits</h2>
                    <p>This application relies on OpenAI's API which has its own rate limits. Please be mindful of the following:</p>
                    <ul>
                        <li>There may be limits on the number of requests you can make within a time period</li>
                        <li>Token usage is tracked and displayed in the response</li>
                        <li>Processing large video files may take more time than images</li>
                    </ul>
                </section>

                <section id="endpoints" class="section">
                    <h2>API Endpoints</h2>
                    
                    <div id="endpoint-home" class="endpoint">
                        <div class="endpoint-header">
                            <div class="endpoint-title">
                                <span class="method get">GET</span>
                                <span class="path">/</span>
                            </div>
                            <p>Serves the main HTML interface for the application.</p>
                        </div>
                        <div class="endpoint-body">
                            <h3>Response</h3>
                            <p>Returns the HTML page for interacting with the API through a user interface.</p>
                            
                            <h4>Status Codes</h4>
                            <table>
                                <tr>
                                    <th>Status Code</th>
                                    <th>Description</th>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-200">200</span></td>
                                    <td>OK - The request was successful</td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <div id="endpoint-docs" class="endpoint">
                        <div class="endpoint-header">
                            <div class="endpoint-title">
                                <span class="method get">GET</span>
                                <span class="path">/api/docs</span>
                            </div>
                            <p>Serves the API documentation (this page).</p>
                        </div>
                        <div class="endpoint-body">
                            <h3>Response</h3>
                            <p>Returns HTML documentation about API endpoints and usage.</p>
                            
                            <h4>Status Codes</h4>
                            <table>
                                <tr>
                                    <th>Status Code</th>
                                    <th>Description</th>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-200">200</span></td>
                                    <td>OK - The request was successful</td>
                                </tr>
                            </table>
                        </div>
                    </div>

                    <div id="endpoint-analyze" class="endpoint">
                        <div class="endpoint-header">
                            <div class="endpoint-title">
                                <span class="method post">POST</span>
                                <span class="path">/analyze/</span>
                            </div>
                            <p>Processes uploaded media files and generates creative stories in both English and Thai.</p>
                        </div>
                        <div class="endpoint-body">
                            <h3>Request</h3>
                            <p>This endpoint accepts multipart/form-data with the following parameters:</p>
                            
                            <table>
                                <tr>
                                    <th>Parameter</th>
                                    <th>Type</th>
                                    <th>Required</th>
                                    <th>Description</th>
                                </tr>
                                <tr>
                                    <td>files</td>
                                    <td>File(s)</td>
                                    <td>Yes</td>
                                    <td>Media files to analyze. Supports JPG, PNG images (multiple files allowed) or a single MP4 video. Maximum file size: 10MB per image, 50MB for video.</td>
                                </tr>
                                <tr>
                                    <td>prompt</td>
                                    <td>String</td>
                                    <td>No</td>
                                    <td>Optional text prompt to guide the story generation. If not provided, a default prompt will be used.</td>
                                </tr>
                            </table>
                            
                            <h3>Response</h3>
                            <p>Returns a JSON object with the following properties:</p>
                            
                            <pre><code>{
  "english": "English language story generated from the media",
  "thai": "Thai language translation of the story",
  "token_usage": {
    "input_tokens": 123,
    "output_tokens": 456,
    "total_tokens": 579
  }
}</code></pre>
                            
                            <div class="tab-container">
                                <div class="tab-header">
                                    <div class="tab active" onclick="switchTab(event, 'curl-example')">cURL</div>
                                    <div class="tab" onclick="switchTab(event, 'js-example')">JavaScript</div>
                                    <div class="tab" onclick="switchTab(event, 'python-example')">Python</div>
                                </div>
                                <div id="curl-example" class="tab-content active">
                                    <pre><code>curl -X POST http://localhost:8000/analyze/ \\
  -F "files=@/path/to/your/image.jpg" \\
  -F "prompt=Generate a story about this image in the style of Anthony Bourdain"</code></pre>
                                </div>
                                <div id="js-example" class="tab-content">
                                    <pre><code>const formData = new FormData();
formData.append('files', imageFile); // From file input
formData.append('prompt', 'Generate a story about this image in the style of Anthony Bourdain');

fetch('http://localhost:8000/analyze/', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log(data.english); // English story
  console.log(data.thai);    // Thai story
  console.log(data.token_usage); // Token usage statistics
})
.catch(error => console.error('Error:', error));</code></pre>
                                </div>
                                <div id="python-example" class="tab-content">
                                    <pre><code>import requests

url = "http://localhost:8000/analyze/"
files = {'files': open('image.jpg', 'rb')}
data = {'prompt': 'Generate a story about this image in the style of Anthony Bourdain'}

response = requests.post(url, files=files, data=data)
result = response.json()

print(result['english'])
print(result['thai'])
print(result['token_usage'])</code></pre>
                                </div>
                            </div>
                            
                            <h3>Status Codes</h3>
                            <table>
                                <tr>
                                    <th>Status Code</th>
                                    <th>Description</th>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-200">200</span></td>
                                    <td>OK - The request was successful</td>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-400">400</span></td>
                                    <td>Bad Request - Invalid file type, file size exceeds limits, or other client errors</td>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-422">422</span></td>
                                    <td>Unprocessable Entity - The server understands the content type but was unable to process the contained instructions</td>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-429">429</span></td>
                                    <td>Too Many Requests - Rate limit exceeded with the OpenAI API</td>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-500">500</span></td>
                                    <td>Internal Server Error - Something went wrong on the server side</td>
                                </tr>
                                <tr>
                                    <td><span class="status-code status-503">503</span></td>
                                    <td>Service Unavailable - The OpenAI API is temporarily unavailable</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                </section>

                <section id="error-handling" class="section">
                    <h2>Error Handling</h2>
                    <p>The API returns standard HTTP status codes to indicate the success or failure of a request. Error responses include a JSON object with details about what went wrong.</p>
                    
                    <h3>Error Response Format</h3>
                    <pre><code>{
  "detail": "Error message describing what went wrong"
}</code></pre>
                </section>

                <section id="usage-examples" class="section">
                    <h2>Usage Examples</h2>
                    
                    <h3>Analyzing a Single Image</h3>
                    <p>This example demonstrates how to upload a single image and generate a story:</p>
                    <pre><code>curl -X POST http://localhost:8000/analyze/ \\
  -F "files=@/path/to/your/image.jpg"</code></pre>
                    
                    <h3>Analyzing Multiple Images</h3>
                    <p>You can upload multiple images in a single request:</p>
                    <pre><code>curl -X POST http://localhost:8000/analyze/ \\
  -F "files=@/path/to/image1.jpg" \\
  -F "files=@/path/to/image2.jpg" \\
  -F "files=@/path/to/image3.jpg"</code></pre>
                    
                    <h3>Analyzing a Video</h3>
                    <p>You can also upload a video file:</p>
                    <pre><code>curl -X POST http://localhost:8000/analyze/ \\
  -F "files=@/path/to/video.mp4"</code></pre>
                </section>

                <section id="troubleshooting" class="section">
                    <h2>Troubleshooting</h2>
                    <p>If you encounter issues using the API, check the following:</p>
                    <ul>
                        <li>Ensure you're using supported file formats (JPG, PNG for images, MP4 for video)</li>
                        <li>Check file size limits (10MB for images, 50MB for video)</li>
                        <li>For server-side issues, check the application logs</li>
                        <li>If you encounter rate limiting, wait and try again later</li>
                    </ul>
                    
                    <h3>Common Issues</h3>
                    <div class="notes-box">
                        <h4><i class="fas fa-exclamation-circle"></i> File Too Large</h4>
                        <p>If you receive a 400 Bad Request error, your file may exceed the size limit. Try compressing your images or videos before uploading.</p>
                    </div>
                    
                    <div class="notes-box">
                        <h4><i class="fas fa-exclamation-circle"></i> Rate Limiting</h4>
                        <p>If you receive a 429 Too Many Requests error, you've exceeded the OpenAI API rate limits. Wait a few minutes before trying again.</p>
                    </div>
                </section>
            </main>
        </div>

        <footer>
            <p>&copy; 2025 ImgStory | Media Analysis Story Generator API</p>
        </footer>

        <script>
            function scrollToSection(sectionId) {
                document.getElementById(sectionId).scrollIntoView({ behavior: 'smooth' });
                
                // Update active sidebar item
                const sidebarItems = document.querySelectorAll('.sidebar-item');
                sidebarItems.forEach(item => {
                    item.classList.remove('active');
                });
                
                // Find and activate the clicked item
                const clickedItem = Array.from(sidebarItems).find(
                    item => item.getAttribute('onclick').includes(sectionId)
                );
                if (clickedItem) {
                    clickedItem.classList.add('active');
                }
            }
            
            function switchTab(event, tabId) {
                // Hide all tab content
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(content => {
                    content.classList.remove('active');
                });
                
                // Remove active class from all tabs
                const tabs = document.querySelectorAll('.tab');
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show the selected tab content and activate the tab
                document.getElementById(tabId).classList.add('active');
                event.currentTarget.classList.add('active');
            }
        </script>
    </body>
    </html>
    """ 