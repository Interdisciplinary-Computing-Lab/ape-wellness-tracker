// Ape Profile Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize pie chart
    initializePieChart();
    
    // Initialize swelling slider
    initializeSwellingSlider();
    
    // Initialize notes form
    initializeNotesForm();
    
    // Add hover effects to buttons
    addButtonHoverEffects();
});

// Initialize the nutrition pie chart
function initializePieChart() {
    const ctx = document.getElementById('nutritionPieChart');
    if (!ctx) return;
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Fruit', 'Protein'],
            datasets: [{
                data: [210, 100], // Banana (210) + Cabbage (22) = 232, Egg (78) = 78
                backgroundColor: [
                    '#28a745', // Green for fruit
                    '#ffc107'  // Yellow for protein
                ],
                borderWidth: 0,
                cutout: '60%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value} cal (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize swelling slider functionality
function initializeSwellingSlider() {
    const slider = document.getElementById('swellingSlider');
    const levelDisplay = document.getElementById('swellingLevel');
    
    if (!slider || !levelDisplay) return;
    
    // Update display when slider changes
    slider.addEventListener('input', function() {
        levelDisplay.textContent = this.value;
        
        // Add visual feedback based on level
        const level = parseInt(this.value);
        levelDisplay.className = 'fw-bold';
        
        if (level === 0) {
            levelDisplay.style.color = '#28a745'; // Green
        } else if (level === 1) {
            levelDisplay.style.color = '#ffc107'; // Yellow
        } else if (level === 2) {
            levelDisplay.style.color = '#fd7e14'; // Orange
        } else if (level === 3) {
            levelDisplay.style.color = '#dc3545'; // Red
        }
    });
    
    // Trigger initial update
    slider.dispatchEvent(new Event('input'));
}

// Initialize notes form functionality
function initializeNotesForm() {
    const noteForm = document.getElementById('noteForm');
    const noteTextarea = document.getElementById('noteTextarea');
    const recentNotes = document.getElementById('recentNotes');
    
    if (!noteForm || !noteTextarea || !recentNotes) return;
    
    noteForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const noteText = noteTextarea.value.trim();
        if (!noteText) {
            showAlert('Please enter a note before posting.', 'warning');
            return;
        }
        
        // Create new note element
        const newNote = createNoteElement(noteText);
        
        // Add animation class
        newNote.classList.add('new');
        
        // Insert at the top of recent notes
        recentNotes.insertBefore(newNote, recentNotes.firstChild);
        
        // Clear the textarea
        noteTextarea.value = '';
        
        // Remove animation class after animation completes
        setTimeout(() => {
            newNote.classList.remove('new');
        }, 300);
        
        // Show success message
        showAlert('Note posted successfully!', 'success');
        
        // Simulate saving to database (in real app, this would be an AJAX call)
        saveNoteToDatabase(noteText);
    });
}

// Create a new note element
function createNoteElement(noteText) {
    const noteDiv = document.createElement('div');
    noteDiv.className = 'note-item border-start border-primary ps-3 mb-3';
    
    const currentTime = new Date();
    const timeString = currentTime.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
    
    noteDiv.innerHTML = `
        <p class="mb-1">${escapeHtml(noteText)}</p>
        <small class="text-muted">
            <i class="fas fa-user me-1"></i>Added by: Tech 1 
            <i class="fas fa-calendar me-1 ms-2"></i>${timeString}
        </small>
    `;
    
    return noteDiv;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Save note to database (simulated)
function saveNoteToDatabase(noteText) {
    // In a real application, this would be an AJAX call to the backend
    console.log('Saving note to database:', noteText);
    
    // Simulate API call
    setTimeout(() => {
        console.log('Note saved successfully');
    }, 500);
}

// Add hover effects to buttons
function addButtonHoverEffects() {
    const buttons = document.querySelectorAll('.btn, .badge');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(alertDiv);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// Update status buttons (if needed for dynamic updates)
function updateStatusButtons(status) {
    const statusButtons = document.querySelectorAll('.status-buttons .badge');
    
    statusButtons.forEach(button => {
        if (button.textContent === status) {
            button.style.transform = 'scale(1.1)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 200);
        }
    });
}

// Refresh nutrition data (for real-time updates)
function refreshNutritionData() {
    // In a real application, this would fetch updated data from the server
    console.log('Refreshing nutrition data...');
    
    // Simulate API call
    setTimeout(() => {
        console.log('Nutrition data updated');
        // Update the pie chart and table here
    }, 1000);
}

// Handle window resize for responsive design
window.addEventListener('resize', function() {
    // Recalculate chart size if needed
    const chart = Chart.getChart('nutritionPieChart');
    if (chart) {
        chart.resize();
    }
});

// Export functions for potential use in other scripts
window.ApeProfile = {
    initializePieChart,
    initializeSwellingSlider,
    initializeNotesForm,
    showAlert,
    updateStatusButtons,
    refreshNutritionData
}; 