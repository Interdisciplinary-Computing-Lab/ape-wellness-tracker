// Log Feeding Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize ape selection
    initializeApeSelection();
    
    // Initialize quick add buttons
    initializeQuickAddButtons();
    
    // Initialize add food form
    initializeAddFoodForm();
    
    // Initialize feeding table
    initializeFeedingTable();
    
    // Initialize quantity and calories controls
    initializeQuantityControls();
    
    // Add hover effects
    addHoverEffects();
});

// Initialize ape selection functionality
function initializeApeSelection() {
    const apeAvatars = document.querySelectorAll('.ape-avatar');
    
    apeAvatars.forEach(avatar => {
        avatar.addEventListener('click', function() {
            const apeId = this.getAttribute('data-ape-id');
            
            // Skip if it's the "More" button
            if (!apeId) return;
            
            // Toggle active state
            this.classList.toggle('active');
            
            // Update avatar appearance
            const avatarCircle = this.querySelector('.avatar-circle');
            if (this.classList.contains('active')) {
                avatarCircle.className = 'avatar-circle bg-primary text-white';
            } else {
                avatarCircle.className = 'avatar-circle bg-secondary text-white';
            }
            
            // Show feedback
            const apeName = this.querySelector('small').textContent;
            const isActive = this.classList.contains('active');
            console.log(`${apeName} ${isActive ? 'selected' : 'deselected'}`);
        });
    });
}

// Initialize quick add buttons
function initializeQuickAddButtons() {
    const quickAddButtons = document.querySelectorAll('.quick-add-btn');
    
    quickAddButtons.forEach(button => {
        button.addEventListener('click', function() {
            const food = this.getAttribute('data-food');
            const calories = parseInt(this.getAttribute('data-calories'));
            
            // Add to feeding table
            addFoodToTable(food, calories, 1);
            
            // Show feedback
            showAlert(`${food} added to feeding`, 'success');
            
            // Add visual feedback
            this.classList.add('success-animation');
            setTimeout(() => {
                this.classList.remove('success-animation');
            }, 500);
        });
    });
}

// Initialize add food form
function initializeAddFoodForm() {
    const addFoodForm = document.getElementById('addFoodForm');
    const foodSelect = document.getElementById('foodSelect');
    const quantityInput = document.getElementById('quantityInput');
    const caloriesInput = document.getElementById('caloriesInput');
    
    if (!addFoodForm) return;
    
    // Auto-populate calories when food is selected
    if (foodSelect) {
        foodSelect.addEventListener('change', function() {
            const selectedFood = this.value;
            const calories = getCaloriesForFood(selectedFood);
            if (calories && caloriesInput) {
                caloriesInput.value = calories;
            }
        });
    }
    
    // Handle form submission
    addFoodForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const food = foodSelect.value;
        const quantity = parseInt(quantityInput.value);
        const calories = parseInt(caloriesInput.value);
        
        if (!food) {
            showAlert('Please select a food item', 'warning');
            return;
        }
        
        if (quantity <= 0) {
            showAlert('Quantity must be greater than 0', 'warning');
            return;
        }
        
        if (calories < 0) {
            showAlert('Calories cannot be negative', 'warning');
            return;
        }
        
        // Add to feeding table
        addFoodToTable(food, calories, quantity);
        
        // Reset form
        foodSelect.value = '';
        quantityInput.value = '1';
        caloriesInput.value = '42';
        
        // Show success message
        showAlert(`${food} added to feeding`, 'success');
    });
}

// Initialize feeding table functionality
function initializeFeedingTable() {
    const clearAllBtn = document.getElementById('clearAllBtn');
    const saveFeedingBtn = document.getElementById('saveFeedingBtn');
    
    // Clear all button
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to clear all items?')) {
                clearFeedingTable();
                showAlert('All items cleared', 'info');
            }
        });
    }
    
    // Save feeding button
    if (saveFeedingBtn) {
        saveFeedingBtn.addEventListener('click', function() {
            saveFeeding();
        });
    }
    
    // Initialize remove buttons for existing items
    initializeRemoveButtons();
}

// Initialize quantity and calories controls
function initializeQuantityControls() {
    const decreaseQty = document.getElementById('decreaseQty');
    const increaseQty = document.getElementById('increaseQty');
    const quantityInput = document.getElementById('quantityInput');
    
    const decreaseCals = document.getElementById('decreaseCals');
    const increaseCals = document.getElementById('increaseCals');
    const caloriesInput = document.getElementById('caloriesInput');
    
    // Quantity controls
    if (decreaseQty && quantityInput) {
        decreaseQty.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue > 1) {
                quantityInput.value = currentValue - 1;
            }
        });
    }
    
    if (increaseQty && quantityInput) {
        increaseQty.addEventListener('click', function() {
            const currentValue = parseInt(quantityInput.value);
            if (currentValue < 99) {
                quantityInput.value = currentValue + 1;
            }
        });
    }
    
    // Calories controls
    if (decreaseCals && caloriesInput) {
        decreaseCals.addEventListener('click', function() {
            const currentValue = parseInt(caloriesInput.value);
            if (currentValue > 0) {
                caloriesInput.value = currentValue - 1;
            }
        });
    }
    
    if (increaseCals && caloriesInput) {
        increaseCals.addEventListener('click', function() {
            const currentValue = parseInt(caloriesInput.value);
            if (currentValue < 999) {
                caloriesInput.value = currentValue + 1;
            }
        });
    }
}

// Add food to the feeding table
function addFoodToTable(food, calories, quantity) {
    const tableBody = document.getElementById('feedingTableBody');
    if (!tableBody) return;
    
    const total = calories * quantity;
    const rowIndex = tableBody.children.length;
    
    const newRow = document.createElement('tr');
    newRow.className = 'new';
    newRow.innerHTML = `
        <td>${escapeHtml(food)}</td>
        <td>${calories}</td>
        <td>${quantity}</td>
        <td>${total}</td>
        <td>
            <button class="btn btn-sm btn-outline-danger remove-item" data-index="${rowIndex}">
                <i class="fas fa-times"></i>
            </button>
        </td>
    `;
    
    tableBody.appendChild(newRow);
    
    // Add click handler to new remove button
    const removeBtn = newRow.querySelector('.remove-item');
    removeBtn.addEventListener('click', function() {
        removeFoodFromTable(this);
    });
    
    // Remove animation class after animation completes
    setTimeout(() => {
        newRow.classList.remove('new');
    }, 300);
    
    // Update total calories
    updateTotalCalories();
}

// Remove food from table
function removeFoodFromTable(button) {
    const row = button.closest('tr');
    if (row) {
        row.style.opacity = '0';
        row.style.transform = 'translateX(-20px)';
        
        setTimeout(() => {
            row.remove();
            updateTotalCalories();
            reindexRemoveButtons();
        }, 200);
    }
}

// Clear all items from feeding table
function clearFeedingTable() {
    const tableBody = document.getElementById('feedingTableBody');
    if (!tableBody) return;
    
    const rows = tableBody.querySelectorAll('tr');
    rows.forEach((row, index) => {
        setTimeout(() => {
            row.style.opacity = '0';
            row.style.transform = 'translateX(-20px)';
            setTimeout(() => row.remove(), 200);
        }, index * 50);
    });
    
    setTimeout(() => {
        updateTotalCalories();
    }, rows.length * 50 + 200);
}

// Update total calories display
function updateTotalCalories() {
    const tableBody = document.getElementById('feedingTableBody');
    const totalDisplay = document.getElementById('totalCalories');
    
    if (!tableBody || !totalDisplay) return;
    
    let total = 0;
    const rows = tableBody.querySelectorAll('tr');
    
    rows.forEach(row => {
        const totalCell = row.querySelector('td:nth-child(4)');
        if (totalCell) {
            total += parseInt(totalCell.textContent) || 0;
        }
    });
    
    totalDisplay.textContent = total;
}

// Reindex remove buttons after removing items
function reindexRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-item');
    removeButtons.forEach((button, index) => {
        button.setAttribute('data-index', index);
    });
}

// Initialize remove buttons for existing items
function initializeRemoveButtons() {
    const removeButtons = document.querySelectorAll('.remove-item');
    removeButtons.forEach(button => {
        button.addEventListener('click', function() {
            removeFoodFromTable(this);
        });
    });
}

// Get calories for a specific food (food database)
function getCaloriesForFood(food) {
    const foodCalories = {
        'apple': 52,
        'banana': 105,
        'cabbage': 22,
        'carrot': 41,
        'egg': 78,
        'orange': 47,
        'pear': 57,
        'tomato': 18
    };
    
    return foodCalories[food.toLowerCase()] || null;
}

// Save feeding to database
function saveFeeding() {
    const selectedApes = getSelectedApes();
    const feedingItems = getFeedingItems();
    
    if (selectedApes.length === 0) {
        showAlert('Please select at least one ape', 'warning');
        return;
    }
    
    if (feedingItems.length === 0) {
        showAlert('Please add at least one food item', 'warning');
        return;
    }
    
    // Show loading state
    const saveBtn = document.getElementById('saveFeedingBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    saveBtn.disabled = true;
    
    // Simulate API call
    setTimeout(() => {
        console.log('Saving feeding for apes:', selectedApes);
        console.log('Feeding items:', feedingItems);
        
        // Reset button
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
        
        // Show success message
        showAlert('Feeding saved successfully!', 'success');
        
        // Clear table
        clearFeedingTable();
        
        // Add success animation
        saveBtn.classList.add('success-animation');
        setTimeout(() => {
            saveBtn.classList.remove('success-animation');
        }, 500);
    }, 1500);
}

// Get selected apes
function getSelectedApes() {
    const selectedAvatars = document.querySelectorAll('.ape-avatar.active');
    const selectedApes = [];
    
    selectedAvatars.forEach(avatar => {
        const apeId = avatar.getAttribute('data-ape-id');
        const apeName = avatar.querySelector('small').textContent;
        if (apeId) {
            selectedApes.push({ id: apeId, name: apeName });
        }
    });
    
    return selectedApes;
}

// Get feeding items from table
function getFeedingItems() {
    const tableBody = document.getElementById('feedingTableBody');
    const items = [];
    
    if (!tableBody) return items;
    
    const rows = tableBody.querySelectorAll('tr');
    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length >= 4) {
            items.push({
                food: cells[0].textContent,
                calories: parseInt(cells[1].textContent),
                quantity: parseInt(cells[2].textContent),
                total: parseInt(cells[3].textContent)
            });
        }
    });
    
    return items;
}

// Add hover effects
function addHoverEffects() {
    const interactiveElements = document.querySelectorAll('.btn, .ape-avatar, .quick-add-btn');
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-1px)';
        });
        
        element.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Show alert message
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for potential use in other scripts
window.LogFeeding = {
    initializeApeSelection,
    initializeQuickAddButtons,
    initializeAddFoodForm,
    initializeFeedingTable,
    addFoodToTable,
    removeFoodFromTable,
    clearFeedingTable,
    saveFeeding,
    getSelectedApes,
    getFeedingItems,
    showAlert
}; 