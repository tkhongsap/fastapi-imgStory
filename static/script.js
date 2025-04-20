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
    const previewContent = document.getElementById('preview-content');

    // Cost constants for gpt-4.1-mini (per 1M tokens)
    const INPUT_COST_USD_PER_MILLION = 0.40;
    const OUTPUT_COST_USD_PER_MILLION = 1.60;
    const USD_TO_THB_RATE = 35.0;
    
    // Files container to keep track of selected files
    let selectedFiles = new DataTransfer();
    
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
        const droppedFiles = dt.files;
        
        // Validate the dropped files
        if (validateFiles(droppedFiles)) {
            // Update selected files
            updateSelectedFiles(droppedFiles);
            
            // Update UI
            updateFileInputUI();
            
            // Generate previews
            generatePreviews();
        }
    }

    // File input visual feedback
    fileInput.addEventListener('change', function() {
        const files = this.files;
        
        // Validate files 
        if (validateFiles(files)) {
            // If valid, update DataTransfer object
            updateSelectedFiles(files);
            
            // Update UI
            updateFileInputUI();
            
            // Generate previews
            generatePreviews();
        }
    });
    
    function updateSelectedFiles(newFiles) {
        // Clear the DataTransfer object if we're uploading a video
        // (since we only allow either multiple images OR one video)
        if (newFiles.length === 1 && newFiles[0].type.startsWith('video/')) {
            selectedFiles = new DataTransfer();
        }
        
        // Add each file to our DataTransfer object
        for (let i = 0; i < newFiles.length; i++) {
            // Only add the file if it's not already in the list
            const file = newFiles[i];
            let isDuplicate = false;
            
            for (let j = 0; j < selectedFiles.files.length; j++) {
                if (selectedFiles.files[j].name === file.name && 
                    selectedFiles.files[j].size === file.size && 
                    selectedFiles.files[j].type === file.type) {
                    isDuplicate = true;
                    break;
                }
            }
            
            if (!isDuplicate) {
                selectedFiles.items.add(file);
            }
        }
        
        // Update the file input with our managed files
        fileInput.files = selectedFiles.files;
    }
    
    function removeFile(fileName) {
        // Find the preview item to animate
        const itemToRemove = Array.from(previewContent.querySelectorAll('.preview-item')).find(
            item => item.querySelector('.remove-item').getAttribute('data-filename') === fileName
        );
        
        // Get the current file count for immediate UI feedback
        const currentCount = selectedFiles.files.length;
        const newCount = currentCount - 1;
        
        // Update file count immediately for responsive UI
        if (newCount > 0) {
            if (newCount <= 3) {
                // Will be updated with actual names in the full refresh
                const tempNames = Array.from(selectedFiles.files)
                    .filter(file => file.name !== fileName)
                    .map(file => file.name)
                    .join(', ');
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${tempNames}`;
            } else {
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${newCount} files selected`;
            }
        }
        
        if (itemToRemove) {
            // Apply the removal animation
            itemToRemove.classList.add('removing');
            
            // Wait for animation to complete before removing from DOM
            setTimeout(() => {
                const newFiles = new DataTransfer();
                
                // Add all files except the one to remove
                for (let i = 0; i < selectedFiles.files.length; i++) {
                    const file = selectedFiles.files[i];
                    if (file.name !== fileName) {
                        newFiles.items.add(file);
                    }
                }
                
                // Update our file list
                selectedFiles = newFiles;
                fileInput.files = selectedFiles.files;
                
                // Update UI
                updateFileInputUI();
                
                // Regenerate previews with animation
                generatePreviewsWithAnimation();
            }, 300); // Match this to the CSS animation duration
        } else {
            // Fallback if preview item not found
            const newFiles = new DataTransfer();
            
            // Add all files except the one to remove
            for (let i = 0; i < selectedFiles.files.length; i++) {
                const file = selectedFiles.files[i];
                if (file.name !== fileName) {
                    newFiles.items.add(file);
                }
            }
            
            // Update our file list
            selectedFiles = newFiles;
            fileInput.files = selectedFiles.files;
            
            // Update UI
            updateFileInputUI();
            
            // Regenerate previews
            generatePreviews();
        }
    }
    
    function validateFiles(files) {
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
            const hasExistingVideo = Array.from(selectedFiles.files).some(file => allowedVideoTypes.includes(file.type));
            
            // If we already have images and trying to add a video, or vice versa
            if (hasVideo && selectedFiles.files.length > 0 && !hasExistingVideo) {
                errorMessage = 'Cannot mix videos and images. Please clear your selection first.';
                hasErrors = true;
            } else if (hasExistingVideo && !hasVideo && selectedFiles.files.length > 0) {
                errorMessage = 'Cannot mix videos and images. Please clear your selection first.';
                hasErrors = true;
            }
            // Make sure we don't have both video and images in new selection
            else if (hasVideo && files.length > 1) {
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
                // Scroll to error message
                errorDiv.scrollIntoView({ behavior: 'smooth' });
                return false;
            }
            
            return true;
        }
        
        return false;
    }
    
    function generatePreviewsWithAnimation() {
        // Clear current previews
        clearPreview();
        
        if (selectedFiles.files.length === 0) {
            uploadArea.classList.remove('has-files');
            uploadArea.classList.remove('has-video');
            return;
        }
        
        // Add has-files class to show we have files
        uploadArea.classList.add('has-files');
        
        // Check if we have a video or images
        const hasVideo = Array.from(selectedFiles.files).some(file => file.type.startsWith('video/'));
        
        // Add single-video class if we have a video
        if (hasVideo) {
            previewContent.classList.add('single-video');
            uploadArea.classList.add('has-video');
        } else {
            previewContent.classList.remove('single-video');
            uploadArea.classList.remove('has-video');
        }
        
        // Generate preview for each file with animation
        for (let i = 0; i < selectedFiles.files.length; i++) {
            const file = selectedFiles.files[i];
            const fileReader = new FileReader();
            
            fileReader.onload = function(e) {
                const fileType = file.type;
                const fileUrl = e.target.result;
                const filePreview = document.createElement('div');
                filePreview.className = 'preview-item reflowing';
                
                // Format file size
                const fileSize = formatFileSize(file.size);
                
                if (fileType.startsWith('image/')) {
                    // Image preview
                    filePreview.innerHTML = `
                        <img src="${fileUrl}" alt="${file.name}">
                        <button class="remove-item" data-filename="${file.name}" title="Remove file">
                            <i class="fas fa-xmark fa-xs"></i>
                        </button>
                        <div class="file-info">${file.name} (${fileSize})</div>
                    `;
                } else if (fileType.startsWith('video/')) {
                    // Video preview
                    filePreview.innerHTML = `
                        <video controls preload="metadata">
                            <source src="${fileUrl}" type="${fileType}">
                            Your browser does not support the video tag.
                        </video>
                        <button class="remove-item" data-filename="${file.name}" title="Remove file">
                            <i class="fas fa-xmark fa-xs"></i>
                        </button>
                        <div class="file-info">${file.name} (${fileSize})</div>
                    `;
                    
                    // Video load event
                    const video = filePreview.querySelector('video');
                    video.addEventListener('loadedmetadata', function() {
                        // Adjust container based on video dimensions if needed
                        if (video.videoHeight > 0 && video.videoWidth > 0) {
                            // Set a reasonable max height
                            const maxHeight = Math.min(video.videoHeight, 450);
                            uploadArea.style.maxHeight = (maxHeight + 150) + 'px'; // Add extra space for controls and info
                        }
                    });
                }
                
                previewContent.appendChild(filePreview);
                
                // Add event listener to remove button
                const removeButton = filePreview.querySelector('.remove-item');
                removeButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    const fileName = this.getAttribute('data-filename');
                    removeFile(fileName);
                });
                
                // Remove the animation class after animation completes
                setTimeout(() => {
                    filePreview.classList.remove('reflowing');
                }, 300);
            };
            
            // Read the file as data URL
            fileReader.readAsDataURL(file);
        }
    }
    
    // Replace the original generatePreviews function with our animated version
    const generatePreviews = generatePreviewsWithAnimation;
    
    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + ' B';
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(1) + ' KB';
        } else {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
    }
    
    function clearPreview() {
        previewContent.innerHTML = '';
        // Reset the upload area styles when clearing
        if (selectedFiles.files.length === 0) {
            uploadArea.classList.remove('has-files');
            uploadArea.classList.remove('has-video');
            uploadArea.style.maxHeight = '';
            previewContent.classList.remove('single-video');
        }
    }
    
    function updateFileInputUI() {
        if (selectedFiles.files.length > 0) {
            const fileCount = selectedFiles.files.length;
            // Update file note with file names if fewer than 3 files
            if (fileCount <= 3) {
                const fileNames = Array.from(selectedFiles.files)
                    .map(file => file.name)
                    .join(', ');
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${fileNames}`;
            } else {
                fileNote.innerHTML = `<i class="fas fa-check-circle" style="color: var(--success-color);"></i> ${fileCount} files selected`;
            }
        } else {
            fileNote.innerHTML = '<i class="fas fa-info-circle"></i> Select multiple images or one video';
            uploadArea.classList.remove('has-files');
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

        // Basic validation: Ensure at least one file is selected
        if (!selectedFiles.files || selectedFiles.files.length === 0) {
            errorP.textContent = 'Please select at least one media file.';
            errorDiv.style.display = 'block';
            resultsDiv.style.display = 'none'; // Hide results
            return;
        }

        const formData = new FormData(form);
        
        // Replace the form's files with our managed files
        formData.delete('files'); // Remove the original files
        for (let i = 0; i < selectedFiles.files.length; i++) {
            formData.append('files', selectedFiles.files[i]);
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
        
        // Reset file input and selected files
        fileInput.value = '';
        selectedFiles = new DataTransfer();
        updateFileInputUI();
        clearPreview();
        
        // Scroll back to upload area
        uploadArea.scrollIntoView({ behavior: 'smooth' });
    });
}); 