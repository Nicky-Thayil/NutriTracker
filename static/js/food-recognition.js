// Food Recognition functionality using camera capture

let foodRecognitionStream = null;
let capturedImageData = null;

// Start food recognition camera
async function startFoodRecognition() {
    try {
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('foodRecognitionModal'));
        modal.show();

        // Clear any previous results
        document.getElementById('foodResult').innerHTML = '';

        // Get video element
        const videoElement = document.getElementById('foodVideo');

        // Request camera access
        try {
            const constraints = {
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: { ideal: 'environment' } // Prefer back camera
                }
            };

            foodRecognitionStream = await navigator.mediaDevices.getUserMedia(constraints);
            videoElement.srcObject = foodRecognitionStream;

        } catch (err) {
            console.error('Camera access error:', err);
            showFoodRecognitionError('Camera access denied or not available. Please ensure you have granted camera permissions.');
        }

    } catch (error) {
        console.error('Food recognition initialization error:', error);
        showFoodRecognitionError('Failed to initialize camera. Please try again.');
    }
}

// Capture food image
function captureFood() {
    try {
        const videoElement = document.getElementById('foodVideo');
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        // Set canvas dimensions to match video
        canvas.width = videoElement.videoWidth || 640;
        canvas.height = videoElement.videoHeight || 480;

        // Draw current video frame to canvas
        context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

        // Convert to blob
        canvas.toBlob(async (blob) => {
            if (!blob) {
                showFoodRecognitionError('Failed to capture image. Please try again.');
                return;
            }

            // Show loading state
            document.getElementById('foodResult').innerHTML = `
                <div class="alert alert-info">
                    <div class="spinner-border spinner-border-sm me-2" role="status"></div>
                    Analyzing food image...
                </div>
            `;

            // Stop video stream
            stopFoodRecognition();

            // Send image to server for recognition
            const formData = new FormData();
            formData.append('image', blob, 'food-image.jpg');

            try {
                const response = await fetch('/recognize-food', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.error) {
                    showFoodRecognitionError(data.error);
                } else {
                    showFoodRecognitionSuccess(data);
                }

            } catch (error) {
                console.error('Food recognition error:', error);
                showFoodRecognitionError('Failed to analyze image. Please try again.');
            }

        }, 'image/jpeg', 0.8);

    } catch (error) {
        console.error('Capture error:', error);
        showFoodRecognitionError('Failed to capture image. Please try again.');
    }
}

// Show food recognition success
function showFoodRecognitionSuccess(data) {
    const resultDiv = document.getElementById('foodResult');
    
    let suggestionsHtml = '';
    if (data.suggestions && data.suggestions.length > 0) {
        suggestionsHtml = `
            <h6 class="mt-3">Search suggestions:</h6>
            <div class="d-grid gap-2">
        `;
        
        data.suggestions.forEach(suggestion => {
            suggestionsHtml += `
                <button type="button" class="btn btn-outline-primary btn-sm" onclick="searchForFood('${suggestion}')">
                    ${suggestion}
                </button>
            `;
        });
        
        suggestionsHtml += '</div>';
    }

    resultDiv.innerHTML = `
        <div class="alert alert-success">
            <h6 class="alert-heading">Food Recognized!</h6>
            <p class="mb-2">We think this might be: <strong>${data.recognized}</strong></p>
            ${suggestionsHtml}
            <div class="mt-3">
                <button type="button" class="btn btn-primary btn-sm" onclick="searchForFood('${data.recognized}')">
                    <i class="bi bi-search"></i> Search for "${data.recognized}"
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm ms-2" onclick="startFoodRecognition()">
                    <i class="bi bi-camera"></i> Take Another Photo
                </button>
            </div>
        </div>
    `;
}

// Show food recognition error
function showFoodRecognitionError(message) {
    document.getElementById('foodResult').innerHTML = `
        <div class="alert alert-warning">
            <i class="bi bi-exclamation-triangle"></i> ${message}
            <div class="mt-2">
                <button type="button" class="btn btn-outline-primary btn-sm" onclick="startFoodRecognition()">
                    <i class="bi bi-arrow-clockwise"></i> Try Again
                </button>
                <button type="button" class="btn btn-outline-secondary btn-sm ms-2" onclick="showManualFoodSearch()">
                    <i class="bi bi-search"></i> Search Manually
                </button>
            </div>
        </div>
    `;
}

// Search for recognized food
function searchForFood(foodName) {
    // Close food recognition modal
    bootstrap.Modal.getInstance(document.getElementById('foodRecognitionModal')).hide();
    
    // If we're on the food log page, populate search and show modal
    if (document.getElementById('addFoodModal')) {
        document.getElementById('foodSearch').value = foodName;
        new bootstrap.Modal(document.getElementById('addFoodModal')).show();
        
        // Trigger search
        searchFood();
    } else {
        // Redirect to food log page with search query
        window.location.href = `/food-log?search=${encodeURIComponent(foodName)}`;
    }
}

// Show manual food search
function showManualFoodSearch() {
    const resultDiv = document.getElementById('foodResult');
    resultDiv.innerHTML = `
        <div class="alert alert-info">
            <h6>Search for Food Manually</h6>
            <div class="input-group mt-2">
                <input type="text" class="form-control" id="manualFoodSearch" placeholder="Enter food name">
                <button class="btn btn-primary" type="button" onclick="searchManualFood()">
                    <i class="bi bi-search"></i> Search
                </button>
            </div>
        </div>
    `;
    document.getElementById('manualFoodSearch').focus();
}

// Search for manually entered food
function searchManualFood() {
    const foodName = document.getElementById('manualFoodSearch').value.trim();
    if (foodName.length < 2) {
        showFoodRecognitionError('Please enter at least 2 characters to search');
        return;
    }
    
    searchForFood(foodName);
}

// Stop food recognition
function stopFoodRecognition() {
    if (foodRecognitionStream) {
        const tracks = foodRecognitionStream.getTracks();
        tracks.forEach(track => track.stop());
        foodRecognitionStream = null;
    }
    
    // Clear video source
    const videoElement = document.getElementById('foodVideo');
    if (videoElement) {
        videoElement.srcObject = null;
    }
}

// Handle modal close
document.addEventListener('DOMContentLoaded', function() {
    const foodModal = document.getElementById('foodRecognitionModal');
    if (foodModal) {
        foodModal.addEventListener('hidden.bs.modal', function() {
            stopFoodRecognition();
        });
    }
});

// Handle Enter key in manual food search
document.addEventListener('keydown', function(e) {
    if (e.target.id === 'manualFoodSearch' && e.key === 'Enter') {
        e.preventDefault();
        searchManualFood();
    }
});

// Camera permission helper
async function checkCameraPermission() {
    try {
        const permission = await navigator.permissions.query({ name: 'camera' });
        return permission.state;
    } catch (error) {
        console.log('Permission API not supported');
        return 'unknown';
    }
}

// Enhanced food recognition with multiple attempts
let recognitionAttempts = 0;
const maxRecognitionAttempts = 3;

function enhancedCaptureFood() {
    recognitionAttempts++;
    
    if (recognitionAttempts <= maxRecognitionAttempts) {
        captureFood();
    } else {
        showFoodRecognitionError('Unable to recognize food after multiple attempts. Please try manual search.');
        recognitionAttempts = 0;
    }
}

// Food recognition tips
function showFoodRecognitionTips() {
    const resultDiv = document.getElementById('foodResult');
    resultDiv.innerHTML = `
        <div class="alert alert-info">
            <h6><i class="bi bi-lightbulb"></i> Tips for better food recognition:</h6>
            <ul class="small mb-0">
                <li>Ensure good lighting</li>
                <li>Keep the food clearly visible in the frame</li>
                <li>Avoid shadows and reflections</li>
                <li>Hold the camera steady</li>
                <li>Try to isolate the main food item</li>
            </ul>
            <button type="button" class="btn btn-primary btn-sm mt-2" onclick="startFoodRecognition()">
                <i class="bi bi-camera"></i> Got it, let's try!
            </button>
        </div>
    `;
}

// Fallback for devices without camera support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.warn('Camera not supported, will use manual food search');
    
    // Override startFoodRecognition for devices without camera
    window.startFoodRecognition = function() {
        const modal = new bootstrap.Modal(document.getElementById('foodRecognitionModal'));
        modal.show();
        showManualFoodSearch();
    };
}

// Image quality enhancement
function enhanceImageQuality(canvas, context) {
    // Apply basic image enhancement
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    // Simple contrast enhancement
    const contrast = 1.2;
    const brightness = 10;
    
    for (let i = 0; i < data.length; i += 4) {
        // Red
        data[i] = Math.min(255, Math.max(0, contrast * data[i] + brightness));
        // Green
        data[i + 1] = Math.min(255, Math.max(0, contrast * data[i + 1] + brightness));
        // Blue
        data[i + 2] = Math.min(255, Math.max(0, contrast * data[i + 2] + brightness));
        // Alpha remains unchanged
    }
    
    context.putImageData(imageData, 0, 0);
}
