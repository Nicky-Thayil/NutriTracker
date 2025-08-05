// Global application JavaScript

// Initialize tooltips and popovers
document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                const alertInstance = bootstrap.Alert.getOrCreateInstance(alert);
                alertInstance.close();
            }, 5000);
        }
    });
});

// Utility functions
const NutriTracker = {
    // Format date for display
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    },

    // Format number with decimal places
    formatNumber: function(number, decimals = 1) {
        return Number(number).toFixed(decimals);
    },

    // Show loading state
    showLoading: function(element) {
        if (element) {
            element.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
            element.disabled = true;
        }
    },

    // Hide loading state
    hideLoading: function(element, originalText) {
        if (element) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    },

    // Show error message
    showError: function(message, container = null) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="bi bi-exclamation-triangle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        if (container) {
            container.innerHTML = alertHtml;
        } else {
            // Add to top of main content
            const main = document.querySelector('main');
            if (main) {
                main.insertAdjacentHTML('afterbegin', `<div class="container mt-3">${alertHtml}</div>`);
            }
        }
    },

    // Show success message
    showSuccess: function(message, container = null) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                <i class="bi bi-check-circle"></i> ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        if (container) {
            container.innerHTML = alertHtml;
        } else {
            // Add to top of main content
            const main = document.querySelector('main');
            if (main) {
                main.insertAdjacentHTML('afterbegin', `<div class="container mt-3">${alertHtml}</div>`);
            }
        }
    },

    // Validate form data
    validateForm: function(form) {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                input.classList.remove('is-invalid');
            }
        });

        return isValid;
    },

    // Local storage helpers
    storage: {
        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.warn('Local storage not available:', e);
            }
        },

        get: function(key) {
            try {
                const value = localStorage.getItem(key);
                return value ? JSON.parse(value) : null;
            } catch (e) {
                console.warn('Error reading from local storage:', e);
                return null;
            }
        },

        remove: function(key) {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.warn('Error removing from local storage:', e);
            }
        }
    },

    // Cache food search results
    foodCache: {
        cache: new Map(),
        maxSize: 100,

        get: function(query) {
            return this.cache.get(query.toLowerCase());
        },

        set: function(query, results) {
            const key = query.toLowerCase();
            if (this.cache.size >= this.maxSize) {
                // Remove oldest entry
                const firstKey = this.cache.keys().next().value;
                this.cache.delete(firstKey);
            }
            this.cache.set(key, results);
        },

        clear: function() {
            this.cache.clear();
        }
    }
};

// Make NutriTracker globally available
window.NutriTracker = NutriTracker;

// Service Worker registration for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // Note: Service worker file not implemented in this MVP
        // but could be added for offline food logging
        console.log('Service Worker support detected');
    });
}

// Handle network status
window.addEventListener('online', function() {
    NutriTracker.showSuccess('Connection restored');
});

window.addEventListener('offline', function() {
    NutriTracker.showError('No internet connection. Some features may be limited.');
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('foodSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
});
