    return document.getElementById('dateFilterForm');
}

function updateCustomDateVisibility(openPicker) {
    const rangeSelect = document.getElementById('range');
    const customDateGroup = document.getElementById('customDateGroup');
    const customRangeGroup = document.getElementById('customRangeGroup');
    const dateInput = document.getElementById('date');
    const startDateInput = document.getElementById('start_date');

    if (!rangeSelect || !customDateGroup || !customRangeGroup) {
        return rangeSelect ? rangeSelect.value : '';
    }

    customDateGroup.style.display = 'none';
    customRangeGroup.style.display = 'none';

    if (rangeSelect.value === 'custom') {
        customDateGroup.style.display = 'block';
        if (openPicker && dateInput) {
            setTimeout(function() {
                dateInput.focus();
            }, 150);
        }
    } else if (rangeSelect.value === 'custom_range') {
        customRangeGroup.style.display = 'block';
        if (openPicker && startDateInput) {
            setTimeout(function() {
                startDateInput.focus();
            }, 150);
        }
    }

    return rangeSelect.value;
}

function submitDateFilterForm() {
    const dateFilterForm = getDateFilterForm();
    if (dateFilterForm) {
        dateFilterForm.submit();
    }
}

function onRangeSelectChange() {
    const range = updateCustomDateVisibility(true);
    if (range !== 'custom' && range !== 'custom_range') {
        submitDateFilterForm();
    }
}

// Auto-submit when date is selected for single custom date
function handleDateChange() {
    // Small delay to ensure the date value is properly set
    setTimeout(() => {
        submitDateFilterForm();
    }, 100);
}

// Auto-submit when both start and end dates are selected for custom range
function handleRangeChange() {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    
    // Only auto-submit if both dates are selected
    if (startDate && endDate) {
        setTimeout(submitDateFilterForm, 100);
    }
}

function closeMobileSidebar() {
    document.body.classList.remove('sidebar-open', 'sidebar-is-opening');
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Trigger file download in the browser
function forceDownload(url) {
    if (!url) {
        alert('Error: No download URL provided.');
        return;
    }
    try {
        const a = document.createElement('a');
        a.href = url;
        a.download = '';
        a.style.display = 'none';
        document.body.appendChild(a);
        setTimeout(function() {
            try {
                a.click();
            } catch (clickError) {
                window.open(url, '_blank');
            }
            setTimeout(function() {
                if (a.parentNode) {
                    document.body.removeChild(a);
                }
            }, 100);
        }, 10);
    } catch (e) {
        window.open(url, '_blank');
    }
}

function downloadViaIframe(url) {
    const iframe = document.createElement('iframe');
    iframe.style.position = 'absolute';
    iframe.style.top = '-9999px';
    iframe.style.left = '-9999px';
    iframe.style.width = '1px';
    iframe.style.height = '1px';
    iframe.style.border = 'none';
    iframe.style.visibility = 'hidden';
    iframe.src = url;
    document.body.appendChild(iframe);
    
    setTimeout(() => {
        if (iframe.parentNode) {
            document.body.removeChild(iframe);
        }
    }, 5000);
}

// Function to initialize download buttons (can be called multiple times)
function initializeDownloadButtons() {
    try {
        console.log('=== Initializing download buttons ===');
        console.log('Document ready state:', document.readyState);
        
        // Set progress bar widths from data attributes
        document.querySelectorAll('.progress-bar[data-width]').forEach(function(bar) {
            const width = bar.getAttribute('data-width');
            bar.style.width = width + '%';
        });
        
        // Show/hide custom date fields only — do not auto-submit on load (caused reload loop)
        updateCustomDateVisibility(false);
        closeMobileSidebar();
        
        // Add event listeners for auto-submit
        const dateInput = document.getElementById('date');
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        
        if (dateInput) {
            dateInput.addEventListener('change', handleDateChange);
        }
        if (startDateInput) {
            startDateInput.addEventListener('change', handleRangeChange);
        }
        if (endDateInput) {
            endDateInput.addEventListener('change', handleRangeChange);
        }
        
        // Add download handlers for CSV download buttons
        const csvButtons = document.querySelectorAll('.download-csv-btn');
        console.log('Found', csvButtons.length, 'CSV download buttons');
        if (csvButtons.length === 0) {
            console.warn('WARNING: No CSV download buttons found!');
            console.log('Searching for buttons with class "download-csv-btn"');
            console.log('All buttons on page:', document.querySelectorAll('button'));
        }
        csvButtons.forEach(function(btn, index) {
            console.log('Attaching listener to CSV button', index, btn, 'URL:', btn.getAttribute('data-url'));
            
            // Remove any existing listeners by cloning
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            // Attach click handler with both capture and bubble phases
            newBtn.addEventListener('click', function(e) {
                console.log('=== CSV download button clicked! ===', this);
                e.preventDefault();
                e.stopPropagation();
                const url = this.getAttribute('data-url');
                console.log('CSV download URL:', url);
                if (url) {
                    if (typeof forceDownload === 'function') {
                        forceDownload(url);
                    } else {
                        console.error('forceDownload function not found!');
                        window.location.href = url;
                    }
                } else {
                    console.error('No data-url attribute found on CSV button');
                    alert('Error: Download URL not found. Please refresh the page and try again.');
                }
                return false;
            });
        });
        
        // Add download handler for raw data button
        const rawButtons = document.querySelectorAll('.download-raw-btn');
        console.log('Found', rawButtons.length, 'raw data download buttons');
        if (rawButtons.length === 0) {
            console.warn('WARNING: No raw data download buttons found!');
            console.log('Searching for buttons with class "download-raw-btn"');
        }
        rawButtons.forEach(function(btn, index) {
            console.log('Attaching listener to raw data button', index, btn, 'Action:', btn.getAttribute('data-action'));
            
            // Remove any existing listeners by cloning
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            // Prevent form submission if button is in a form
            const form = newBtn.closest('form');
            if (form) {
                form.addEventListener('submit', function(e) {
                    // Prevent form submission if the download button was clicked
                    if (e.submitter === newBtn || (e.target && e.target.contains(newBtn))) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                }, true); // Use capture phase
            }
            
            // Attach click handler with both capture and bubble phases
            newBtn.addEventListener('click', function(e) {
                console.log('=== Raw data download button clicked! ===', this);
                e.preventDefault();
                e.stopPropagation();
                const action = this.getAttribute('data-action');
                const range = this.getAttribute('data-range');
                const date = this.getAttribute('data-date');
                const startDate = this.getAttribute('data-start-date');
                const endDate = this.getAttribute('data-end-date');
                const denormalized = document.getElementById('denormalizedCheck') ? 
                                     (document.getElementById('denormalizedCheck').checked ? 'true' : 'false') : 'false';
                
                if (!action) {
                    console.error('No data-action attribute found on raw data button');
                    alert('Error: Download action not found. Please refresh the page and try again.');
                    return false;
                }
                
                const params = new URLSearchParams({
                    range: range || 'all',
                    date: date || '',
                    start_date: startDate || '',
                    end_date: endDate || '',
                    denormalized: denormalized
                });
                const url = action + '?' + params.toString();
                console.log('Raw data download URL:', url);
                if (typeof forceDownload === 'function') {
                    forceDownload(url);
                } else {
                    console.error('forceDownload function not found!');
                    window.location.href = url;
                }
                return false;
            });
        });
        
        console.log('=== Download button initialization complete ===');
    } catch (error) {
        console.error('Error initializing download buttons:', error);
        console.error('Stack trace:', error.stack);
    }
}

// Initialize on page load - try multiple methods
console.log('Setting up download button initialization...');
console.log('Document ready state:', document.readyState);

if (document.readyState === 'loading') {
    console.log('Document still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOMContentLoaded fired, initializing buttons');
        initializeDownloadButtons();
    });
} else {
    console.log('Document already loaded, initializing buttons immediately');
    initializeDownloadButtons();
}

// Close mobile sidebar when tapping main content (overlay can stick after nav)
document.addEventListener('click', function(e) {
    if (!document.body.classList.contains('sidebar-open')) {
        return;
    }
    if (e.target.closest('.main-sidebar') || e.target.closest('[data-widget="pushmenu"]')) {
        return;
    }
    closeMobileSidebar();
});
