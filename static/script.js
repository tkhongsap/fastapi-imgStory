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
                try {
                    const errorData = await response.json(); 
                    errorMessage = errorData.detail || JSON.stringify(errorData);
                } catch (e) {
                    // If parsing error JSON fails, use the status text
                    errorMessage = `${errorMessage} - ${response.statusText}`;
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
            errorP.textContent = `Error: ${error.message || 'Failed to analyze media. Check console for details.'}`;
            errorDiv.style.display = 'block';
            resultsDiv.style.display = 'none'; // Keep results hidden on error
            
            // Smoothly scroll to error message
            errorDiv.scrollIntoView({ behavior: 'smooth' });
        }
    });
}); 