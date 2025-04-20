document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('upload-form');
    const fileInput = document.getElementById('media-files');
    const loadingIndicator = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const englishCaptionP = document.querySelector('#english-caption p');
    const thaiCaptionP = document.querySelector('#thai-caption p');
    const inputTokensSpan = document.querySelector('#input-tokens');
    const outputTokensSpan = document.querySelector('#output-tokens');
    const costUsdSpan = document.querySelector('#cost-usd');
    const costThbSpan = document.querySelector('#cost-thb');
    const errorDiv = document.getElementById('error-message');
    const errorP = document.querySelector('#error-message p');
    const copyButtons = document.querySelectorAll('.copy-btn');
    const fileInputLabel = document.querySelector('.file-input-label span');
    const fileNote = document.querySelector('.file-note');
    const uploadArea = document.querySelector('.upload-area');
    const retryButton = document.getElementById('retry-button');

    // Cost constants for gpt-4.1-mini (per 1M tokens)
    const INPUT_COST_USD_PER_MILLION = 0.40;
    const OUTPUT_COST_USD_PER_MILLION = 1.60;
    const USD_TO_THB_RATE = 35.0;

    // Drag and drop functionality
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.classList.add('highlight');
    }
    
    function unhighlight() {
        uploadArea.classList.remove('highlight');
    }
    
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        updateFileInputUI(files);
    }

    // File input visual feedback
    fileInput.addEventListener('change', function() {
        updateFileInputUI(this.files);
    });
    
    function updateFileInputUI(files) {
        if (files && files.length > 0) {
            // Validate files
            const maxImageSize = 10 * 1024 * 1024; // 10MB in bytes
            const maxVideoSize = 50 * 1024 * 1024; // 50MB in bytes
            const allowedImageTypes = ['image/jpeg', 'image/jpg', 'image/png'];
            const allowedVideoTypes = ['video/mp4'];
            let hasErrors = false;
            let errorMessage = '';
            
            // Check if we have a video or images
            const hasVideo = Array.from(files).some(file => allowedVideoTypes.includes(file.type));
            
            // Make sure we don't have both video and images
            if (hasVideo && files.length > 1) {
                errorMessage = 'Please upload either a single video or multiple images, not both.';
                hasErrors = true;
            } else if (hasVideo) {
                // Check video size
                const videoFile = Array.from(files).find(file => allowedVideoTypes.includes(file.type));
                if (videoFile.size > maxVideoSize) {
                    errorMessage = `Video file '${videoFile.name}' is too large. Maximum size is 50MB.`;
                    hasErrors = true;
                }
            } else {
                // Check image types and sizes
                const invalidFiles = Array.from(files).filter(file => !allowedImageTypes.includes(file.type));
                if (invalidFiles.length > 0) {
                    const fileNames = invalidFiles.map(f => f.name).join(', ');
                    errorMessage = `Unsupported file type(s): ${fileNames}. Only JPG and PNG images are supported.`;
                    hasErrors = true;
                } else {
                    // Check image sizes
                    const oversizedFiles = Array.from(files).filter(file => file.size > maxImageSize);
                    if (oversizedFiles.length > 0) {
                        const fileNames = oversizedFiles.map(f => f.name).join(', ');
                        errorMessage = `File(s) too large: ${fileNames}. Maximum size per image is 10MB.`;
                        hasErrors = true;
                    }
                }
            }
            
            if (hasErrors) {
                // Display error
                errorP.textContent = errorMessage;
                errorDiv.style.display = 'block';
                fileInput.value = ''; // Reset file input
                fileInputLabel.textContent = 'Choose Files';
                fileNote.innerHTML = '<i class="fas fa-info-circle"></i> Select multiple images or one video';
                // Scroll to error message
                errorDiv.scrollIntoView({ behavior: 'smooth' });
                return;
            }
            
            // If validation passes, update UI
            const fileCount = files.length;
            fileInputLabel.textContent = `${fileCount} file${fileCount > 1 ? 's' : ''} selected`;
            
            // Update file note with file names if fewer than 3 files
            if (fileCount <= 3) {
                const fileNames = Array.from(files)
                    .map(file => file.name)
                    .join(', ');
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${fileNames}`;
            } else {
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${fileCount} files selected`;
            }
        } else {
            fileInputLabel.textContent = 'Choose Files';
            fileNote.innerHTML = '<i class="fas fa-info-circle"></i> Select multiple images or one video';
        }
    }

    // Copy button functionality
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const textToCopy = document.querySelector(`#${targetId} p`).textContent;
            
            navigator.clipboard.writeText(textToCopy)
                .then(() => {
                    // Visual feedback
                    const originalIcon = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i>';
                    this.style.backgroundColor = 'var(--success-color)';
                    this.style.color = 'white';
                    
                    setTimeout(() => {
                        this.innerHTML = originalIcon;
                        this.style.backgroundColor = '';
                        this.style.color = '';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Failed to copy: ', err);
                });
        });
    });

    // Form submission handling
    form.addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent default form submission

        const formData = new FormData(form);

        // Basic validation: Ensure at least one file is selected
        if (!fileInput.files || fileInput.files.length === 0) {
            errorP.textContent = 'Please select at least one media file.';
            errorDiv.style.display = 'block';
            resultsDiv.style.display = 'none'; // Hide results
            return;
        }

        // --- Reset UI --- 
        loadingIndicator.style.display = 'block';
        resultsDiv.style.display = 'none'; // Hide results until ready
        errorDiv.style.display = 'none';
        englishCaptionP.textContent = '...';
        thaiCaptionP.textContent = '...';
        inputTokensSpan.textContent = '0';
        outputTokensSpan.textContent = '0';
        costUsdSpan.textContent = '$0.00';
        costThbSpan.textContent = '฿0.00';

        // Smoothly scroll to loading indicator
        loadingIndicator.scrollIntoView({ behavior: 'smooth' });

        try {
            const response = await fetch('/analyze/', {
                method: 'POST',
                body: formData,
                // No 'Content-Type' header needed; browser sets it for FormData
            });

            loadingIndicator.style.display = 'none'; // Hide loading indicator

            if (!response.ok) {
                let errorMessage = `HTTP error! status: ${response.status}`;
                let errorDetail = '';
                
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || JSON.stringify(errorData);
                    
                    // Handle specific error types
                    if (errorDetail.includes('rate limit') || errorDetail.includes('quota')) {
                        errorMessage = 'OpenAI API rate limit exceeded. Please try again in a few moments.';
                    } else if (errorDetail.includes('file size')) {
                        errorMessage = 'File size too large. Please upload smaller images or videos.';
                    } else if (errorDetail.includes('file type') || errorDetail.includes('unsupported')) {
                        errorMessage = 'Unsupported file type. Please upload JPG, PNG images or MP4 videos.';
                    } else if (response.status === 413) {
                        errorMessage = 'The uploaded file is too large. Please reduce file size and try again.';
                    } else if (response.status === 415) {
                        errorMessage = 'Unsupported media type. Only JPG, PNG images and MP4 videos are supported.';
                    } else if (response.status === 429) {
                        errorMessage = 'Too many requests. Please try again later.';
                    } else if (response.status >= 500) {
                        errorMessage = 'Server error. Our team has been notified. Please try again later.';
                    } else {
                        errorMessage = `Error: ${errorDetail}`;
                    }
                } catch (e) {
                    // If parsing error JSON fails, use the status text with user-friendly message
                    if (response.status === 400) {
                        errorMessage = 'Invalid request. Please check your files and try again.';
                    } else if (response.status === 401 || response.status === 403) {
                        errorMessage = 'Authentication error. Please refresh the page and try again.';
                    } else if (response.status === 404) {
                        errorMessage = 'Service endpoint not found. Please contact support.';
                    } else if (response.status >= 500) {
                        errorMessage = 'Server error. Our team has been notified. Please try again later.';
                    } else {
                        errorMessage = `Error: ${response.status} - ${response.statusText}`;
                    }
                }
                
                throw new Error(errorMessage);
            }

            const data = await response.json();

            // Display results
            englishCaptionP.textContent = data.english || 'No English caption generated.';
            thaiCaptionP.textContent = data.thai || 'No Thai caption generated.';
            
            // Get token counts
            const inputTokens = data.input_tokens || 0;
            const outputTokens = data.output_tokens || 0;
            
            // Calculate costs
            const inputCostUsd = (inputTokens / 1000000) * INPUT_COST_USD_PER_MILLION;
            const outputCostUsd = (outputTokens / 1000000) * OUTPUT_COST_USD_PER_MILLION;
            const totalCostUsd = inputCostUsd + outputCostUsd;
            const totalCostThb = totalCostUsd * USD_TO_THB_RATE;
            
            // Format token counts with thousands separator for display
            const formatter = new Intl.NumberFormat('en-US');
            inputTokensSpan.textContent = formatter.format(inputTokens);
            outputTokensSpan.textContent = formatter.format(outputTokens);
            
            // Display costs with appropriate precision
            // Show more decimal places for very small amounts
            if (totalCostUsd < 0.01) {
                costUsdSpan.textContent = '$' + totalCostUsd.toFixed(6);
                costThbSpan.textContent = '฿' + totalCostThb.toFixed(6);
            } else {
                costUsdSpan.textContent = '$' + totalCostUsd.toFixed(4);
                costThbSpan.textContent = '฿' + totalCostThb.toFixed(4);
            }
            
            resultsDiv.style.display = 'block';
            
            // Smoothly scroll to results
            resultsDiv.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Error submitting form:', error);
            loadingIndicator.style.display = 'none'; // Ensure loading is hidden on error
            
            let errorMessage = error.message || 'Failed to analyze media. Check console for details.';
            
            // Handle network errors
            if (error.name === 'TypeError' && errorMessage.includes('Failed to fetch')) {
                errorMessage = 'Network error. Please check your internet connection and try again.';
            } else if (error.name === 'AbortError') {
                errorMessage = 'Request was aborted. Please try again.';
            } else if (error.name === 'TimeoutError' || errorMessage.includes('timeout')) {
                errorMessage = 'Request timed out. Please try again later.';
            }
            
            // Display the error message
            errorP.textContent = errorMessage;
            errorDiv.style.display = 'block';
            resultsDiv.style.display = 'none'; // Keep results hidden on error
            
            // Smoothly scroll to error message
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }
    });

    // Retry button functionality
    retryButton.addEventListener('click', function() {
        // Hide error message
        errorDiv.style.display = 'none';
        
        // Reset file input
        fileInput.value = '';
        updateFileInputUI(fileInput.files);
        
        // Scroll back to upload area
        uploadArea.scrollIntoView({ behavior: 'smooth' });
    });
}); 