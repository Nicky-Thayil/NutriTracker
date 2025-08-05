// Barcode Scanner functionality using getUserMedia and ZXing library

let barcodeStream = null;
let barcodeScanner = null;

// Load ZXing library dynamically
function loadZXingLibrary() {
    return new Promise((resolve, reject) => {
        if (window.ZXing) {
            resolve(window.ZXing);
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://unpkg.com/@zxing/library@latest/umd/index.min.js';
        script.onload = () => {
            if (window.ZXing) {
                resolve(window.ZXing);
            } else {
                reject(new Error('ZXing library failed to load'));
            }
        };
        script.onerror = () => reject(new Error('Failed to load ZXing library'));
        document.head.appendChild(script);
    });
}

// Start barcode scanner
async function startBarcodeScanner() {
    try {
        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('barcodeModal'));
        modal.show();

        // Clear any previous results
        document.getElementById('barcodeResult').innerHTML = '';

        // Load ZXing library
        const ZXing = await loadZXingLibrary();
        
        // Initialize code reader
        barcodeScanner = new ZXing.BrowserMultiFormatReader();

        // Get video element
        const videoElement = document.getElementById('barcodeVideo');

        // Start scanning
        try {
            const devices = await barcodeScanner.listVideoInputDevices();
            
            if (devices.length === 0) {
                throw new Error('No camera devices found');
            }

            // Prefer back camera on mobile devices
            let selectedDevice = devices[0];
            for (const device of devices) {
                if (device.label.toLowerCase().includes('back') || device.label.toLowerCase().includes('rear')) {
                    selectedDevice = device;
                    break;
                }
            }

            // Start decoding
            barcodeScanner.decodeFromVideoDevice(
                selectedDevice.deviceId,
                videoElement,
                (result, error) => {
                    if (result) {
                        handleBarcodeResult(result.text);
                    }
                    if (error && error.name !== 'NotFoundException') {
                        console.warn('Barcode scan error:', error);
                    }
                }
            );

        } catch (err) {
            console.error('Camera access error:', err);
            showBarcodeError('Camera access denied or not available. Please ensure you have granted camera permissions.');
        }

    } catch (error) {
        console.error('Barcode scanner initialization error:', error);
        showBarcodeError('Failed to initialize barcode scanner. Please try again.');
    }
}

// Handle successful barcode scan
function handleBarcodeResult(barcode) {
    console.log('Barcode detected:', barcode);
    
    // Stop the scanner
    stopBarcodeScanner();
    
    // Show loading state
    document.getElementById('barcodeResult').innerHTML = `
        <div class="alert alert-info">
            <div class="spinner-border spinner-border-sm me-2" role="status"></div>
            Looking up product: ${barcode}
        </div>
    `;

    // Send barcode to server
    fetch('/scan-barcode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ barcode: barcode })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showBarcodeError(data.error);
        } else {
            showBarcodeSuccess(data);
        }
    })
    .catch(error => {
        console.error('Barcode lookup error:', error);
        showBarcodeError('Failed to look up product. Please try again.');
    });
}

// Show barcode scan success
function showBarcodeSuccess(foodData) {
    const resultDiv = document.getElementById('barcodeResult');
    resultDiv.innerHTML = `
        <div class="alert alert-success">
            <h6 class="alert-heading">Product Found!</h6>
            <strong>${foodData.name}</strong>
            ${foodData.brand ? `<br><small class="text-muted">${foodData.brand}</small>` : ''}
            <hr>
            <div class="row text-center">
                <div class="col-6">
                    <strong>${foodData.calories_per_100g || 0}</strong><br>
                    <small>Calories/100g</small>
                </div>
                <div class="col-6">
                    <strong>${foodData.protein_per_100g || 0}g</strong><br>
                    <small>Protein/100g</small>
                </div>
            </div>
            <div class="mt-3">
                <button type="button" class="btn btn-primary" onclick="addScannedFood(${foodData.id}, '${foodData.name}')">
                    <i class="bi bi-plus-circle"></i> Add to Food Log
                </button>
            </div>
        </div>
    `;
}

// Show barcode scan error
function showBarcodeError(message) {
    document.getElementById('barcodeResult').innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-triangle"></i> ${message}
            <div class="mt-2">
                <button type="button" class="btn btn-outline-primary btn-sm" onclick="startBarcodeScanner()">
                    <i class="bi bi-arrow-clockwise"></i> Try Again
                </button>
            </div>
        </div>
    `;
}

// Add scanned food to log
function addScannedFood(foodId, foodName) {
    // Close barcode modal
    bootstrap.Modal.getInstance(document.getElementById('barcodeModal')).hide();
    
    // If we're on the food log page, show the add food modal
    if (document.getElementById('addFoodModal')) {
        // Pre-select the food and show add modal
        document.getElementById('selectedFoodId').value = foodId;
        document.getElementById('selectedFoodName').textContent = foodName;
        document.getElementById('selectedFoodInfo').style.display = 'block';
        document.getElementById('addFoodBtn').disabled = false;
        document.getElementById('foodSearch').value = foodName;
        
        new bootstrap.Modal(document.getElementById('addFoodModal')).show();
    } else {
        // Redirect to food log page with the scanned food
        window.location.href = `/food-log?scanned_food=${foodId}`;
    }
}

// Stop barcode scanner
function stopBarcodeScanner() {
    if (barcodeScanner) {
        barcodeScanner.reset();
        barcodeScanner = null;
    }
    
    // Stop video stream
    const videoElement = document.getElementById('barcodeVideo');
    if (videoElement && videoElement.srcObject) {
        const tracks = videoElement.srcObject.getTracks();
        tracks.forEach(track => track.stop());
        videoElement.srcObject = null;
    }
}

// Handle modal close
document.addEventListener('DOMContentLoaded', function() {
    const barcodeModal = document.getElementById('barcodeModal');
    if (barcodeModal) {
        barcodeModal.addEventListener('hidden.bs.modal', function() {
            stopBarcodeScanner();
        });
    }
});

// Alternative barcode input for devices without camera
function showManualBarcodeInput() {
    const resultDiv = document.getElementById('barcodeResult');
    resultDiv.innerHTML = `
        <div class="alert alert-info">
            <h6>Enter Barcode Manually</h6>
            <div class="input-group mt-2">
                <input type="text" class="form-control" id="manualBarcode" placeholder="Enter barcode number">
                <button class="btn btn-primary" type="button" onclick="lookupManualBarcode()">
                    <i class="bi bi-search"></i> Lookup
                </button>
            </div>
        </div>
    `;
    document.getElementById('manualBarcode').focus();
}

// Lookup manually entered barcode
function lookupManualBarcode() {
    const barcode = document.getElementById('manualBarcode').value.trim();
    if (barcode.length < 8) {
        showBarcodeError('Please enter a valid barcode (at least 8 digits)');
        return;
    }
    
    handleBarcodeResult(barcode);
}

// Handle Enter key in manual barcode input
document.addEventListener('keydown', function(e) {
    if (e.target.id === 'manualBarcode' && e.key === 'Enter') {
        e.preventDefault();
        lookupManualBarcode();
    }
});

// Fallback for devices without camera support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    console.warn('Camera not supported, will use manual barcode entry');
    
    // Override startBarcodeScanner for devices without camera
    window.startBarcodeScanner = function() {
        const modal = new bootstrap.Modal(document.getElementById('barcodeModal'));
        modal.show();
        showManualBarcodeInput();
    };
}
