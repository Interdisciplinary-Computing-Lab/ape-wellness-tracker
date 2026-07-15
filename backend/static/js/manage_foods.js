document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', function() {
            filterByCategory(this.getAttribute('data-category'), this);
        });
    });

    const foodSearchInput = document.getElementById('foodSearch');
    const foodSearchClear = document.getElementById('foodSearchClear');
    if (foodSearchInput) {
        foodSearchInput.addEventListener('input', function() {
            applyFoodFilters();
            updateFoodSearchUi();
        });
        foodSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                clearFoodSearch();
            }
        });
    }
    if (foodSearchClear) {
        foodSearchClear.addEventListener('click', clearFoodSearch);
    }
    updateFoodSearchUi();
});

let currentFoodCategory = 'all';

function itemMatchesCategory(item, category) {
    const itemCategory = item.dataset.category || 'Other';
    if (category === 'all') {
        return true;
    }
    if (category === 'favorites') {
        return item.dataset.favorite === 'true';
    }
    if (category === 'Enrichment Treats') {
        return itemCategory === 'Enrichment Treats' || itemCategory === 'Dried Fruits';
    }
    return itemCategory === category;
}

function applyFoodFilters() {
    const searchInput = document.getElementById('foodSearch');
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const foodItems = document.querySelectorAll('.food-item');
    let visibleCount = 0;

    foodItems.forEach(item => {
        const name = item.dataset.name || '';
        const description = item.dataset.description || '';
        const source = item.dataset.source || '';
        const categoryText = (item.dataset.category || '').toLowerCase();
        const matchesCategory = itemMatchesCategory(item, currentFoodCategory);
        const matchesSearch = !searchTerm ||
            name.includes(searchTerm) ||
            description.includes(searchTerm) ||
            source.includes(searchTerm) ||
            categoryText.includes(searchTerm);

        if (matchesCategory && matchesSearch) {
            item.classList.remove('hidden');
            visibleCount += 1;
        } else {
            item.classList.add('hidden');
        }
    });

    const emptyEl = document.getElementById('foodSearchEmpty');
    if (emptyEl) {
        emptyEl.classList.toggle('d-none', visibleCount > 0);
    }
    return visibleCount;
}

function updateFoodSearchUi() {
    const searchInput = document.getElementById('foodSearch');
    const clearBtn = document.getElementById('foodSearchClear');
    const hint = document.getElementById('foodSearchHint');
    const term = searchInput ? searchInput.value.trim() : '';
    const visible = document.querySelectorAll('.food-item:not(.hidden)').length;
    const total = document.querySelectorAll('.food-item').length;

    if (clearBtn) {
        clearBtn.hidden = term.length === 0;
    }
    if (hint) {
        if (term.length > 0) {
            hint.textContent = visible === 1
                ? 'Showing 1 food'
                : 'Showing ' + visible + ' of ' + total + ' foods';
        } else if (currentFoodCategory !== 'all') {
            hint.textContent = visible === 1
                ? 'Showing 1 food in this category'
                : 'Showing ' + visible + ' foods in this category';
        } else {
            hint.textContent = total + ' foods';
        }
    }
}

function filterByCategory(category, clickedButton) {
    currentFoodCategory = category;
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    let activeBtn = clickedButton;
    if (!activeBtn) {
        document.querySelectorAll('.filter-btn').forEach(btn => {
            if (btn.getAttribute('data-category') === category) {
                activeBtn = btn;
            }
        });
    }
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    applyFoodFilters();
    updateFoodSearchUi();
}

function clearFoodSearch() {
    const searchInput = document.getElementById('foodSearch');
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    applyFoodFilters();
    updateFoodSearchUi();
}

// Add event listeners for edit and delete buttons
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.food-favorite-btn').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            toggleManageFoodFavorite(this);
        });
    });

    // Edit food buttons
    document.querySelectorAll('.edit-food-btn').forEach(button => {
        button.addEventListener('click', function() {
            const recipeId = this.getAttribute('data-id');
            const recipeName = this.getAttribute('data-name');
            const recipeCategory = this.getAttribute('data-category');
            const recipeCalories = this.getAttribute('data-calories');
            const recipeQuantity = this.getAttribute('data-quantity') || '1.0';
            const recipeUnit = this.getAttribute('data-unit') || '';
            const recipeSource = this.getAttribute('data-source') || '';
            const recipeDescription = this.getAttribute('data-description');
            
            // Populate the edit form
            document.getElementById('editFoodName').value = recipeName;
            document.getElementById('editFoodCategory').value = recipeCategory || 'Other';
            document.getElementById('editCalories').value = recipeCalories;
            document.getElementById('editQuantity').value = recipeQuantity;
            document.getElementById('editUnitOfMeasurement').value = recipeUnit;
            document.getElementById('editSource').value = recipeSource;
            document.getElementById('editDescription').value = recipeDescription || '';
            
            // Set the form action
            document.getElementById('editFoodForm').action = `/recipes/${recipeId}/edit`;
            
            // Show the modal
            $('#editFoodModal').modal('show');
        });
    });
    
    // Delete food buttons
    document.querySelectorAll('.delete-food-btn').forEach(button => {
        button.addEventListener('click', function() {
            const recipeId = this.getAttribute('data-id');
            const recipeName = this.getAttribute('data-name');
            
            // Set the food name in the confirmation modal
            document.getElementById('deleteFoodName').textContent = recipeName;
            
            // Set the form action
            document.getElementById('deleteFoodForm').action = `/recipes/${recipeId}/delete`;
            
            // Show the confirmation modal
            $('#deleteFoodModal').modal('show');
        });
    });
});

function updateManageFavoriteUi(foodItem, isFavorite) {
    const favoriteValue = isFavorite ? 'true' : 'false';
    foodItem.dataset.favorite = favoriteValue;
    const starBtn = foodItem.querySelector('.food-favorite-btn');
    if (starBtn) {
        starBtn.dataset.favorite = favoriteValue;
        starBtn.title = isFavorite ? 'Remove from favorites' : 'Add to favorites';
        starBtn.setAttribute('aria-label', starBtn.title);
        const icon = starBtn.querySelector('i');
        if (icon) {
            icon.className = isFavorite ? 'fas fa-star' : 'fas fa-star-o';
        }
    }
}

function updateManageFavoritesFilterCount() {
    const favoritesBtn = document.querySelector('.filter-btn[data-category="favorites"] .filter-count');
    if (!favoritesBtn) {
        return;
    }
    const count = document.querySelectorAll('.food-item[data-favorite="true"]').length;
    favoritesBtn.textContent = '(' + count + ')';
}

function toggleManageFoodFavorite(btn) {
    const recipeId = btn.getAttribute('data-recipe-id');
    if (!recipeId) {
        return;
    }
    fetch('/api/recipes/' + encodeURIComponent(recipeId) + '/favorite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(result => {
        if (!result.ok || !result.data.success) {
            showNotification(result.data.message || 'Could not update favorite', 'error');
            return;
        }
        const foodItem = btn.closest('.food-item');
        if (foodItem) {
            updateManageFavoriteUi(foodItem, result.data.is_favorite);
            updateManageFavoritesFilterCount();
            applyFoodFilters();
            updateFoodSearchUi();
        }
        showNotification(result.data.message, 'success');
    })
    .catch(error => {
        console.error('Error toggling favorite:', error);
        showNotification('Failed to update favorite', 'error');
    });
}

// Show notification function
function showNotification(message, type) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}
