document.getElementById('upload-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent default form submission

    const form = event.target;
    const formData = new FormData(form);
    const filesInput = document.getElementById('media-files');
    const loadingIndicator = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const englishCaptionP = document.querySelector('#english-caption p');
    const thaiCaptionP = document.querySelector('#thai-caption p');
    const errorDiv = document.getElementById('error-message');
    const errorP = document.querySelector('#error-message p');

    // Basic validation: Ensure at least one file is selected
    if (!filesInput.files || filesInput.files.length === 0) {
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
        resultsDiv.style.display = 'block';

    } catch (error) {
        console.error('Error submitting form:', error);
        loadingIndicator.style.display = 'none'; // Ensure loading is hidden on error
        errorP.textContent = `Error: ${error.message || 'Failed to analyze media. Check console for details.'}`;
        errorDiv.style.display = 'block';
        resultsDiv.style.display = 'none'; // Keep results hidden on error
    }
}); 