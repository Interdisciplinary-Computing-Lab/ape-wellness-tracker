/** @file Food catalog search, categories, and quick-add. */
// Global function for inline onclick handlers (most reliable) - defined first
function addFoodFromButton(btn) {
    try {
        if (!requireApeBeforeAddingFood()) {
            return false;
        }

        // Try multiple ways to get the data
        const food = btn.getAttribute('data-food') || btn.dataset.food;
        const caloriesStr = btn.getAttribute('data-calories') || btn.dataset.calories;
        const quantityStr = btn.getAttribute('data-quantity') || btn.dataset.quantity || '1.0';
        const unit = btn.getAttribute('data-unit') || btn.dataset.unit || '';
        const source = btn.getAttribute('data-source') || btn.dataset.source || '';
        const gramsStr = btn.getAttribute('data-grams') || btn.dataset.grams || '0';
        const name = btn.getAttribute('data-name') || btn.dataset.name || food;
        
        const calories = parseInt(caloriesStr, 10);
        const quantity = parseFloat(quantityStr) || 1.0;
        const gramsPerServing = parseFloat(gramsStr) || 0;
        
        if (!name) {
            console.error('Missing food name');
            alert('Error: Missing food name. Please try again.');
            return false;
        }
        
        if (isNaN(calories) || calories <= 0) {
            console.error('Invalid calories:', caloriesStr);
            alert('Error: Invalid calories value. Please try again.');
            return false;
        }
        
        if (isNaN(quantity) || quantity <= 0) {
            console.error('Invalid quantity:', quantityStr);
            alert('Error: Invalid quantity value. Please try again.');
            return false;
        }
        
        addFoodItem(name, calories, quantity, unit, source, gramsPerServing);
        
        // Visual feedback
        btn.classList.add('btn-success');
        setTimeout(() => {
            btn.classList.remove('btn-success');
        }, 500);
        
        return false;
    } catch (error) {
        console.error('Error in addFoodFromButton:', error);
        alert('Error adding food item. Please try again.');
        return false;
    }
}
function foodItemMatchesSearch(item, searchTerm) {
    const name = (item.getAttribute('data-name') || '').toLowerCase();
    const description = (item.getAttribute('data-description') || '').toLowerCase();
    const category = (item.getAttribute('data-category') || '').toLowerCase();
    return name.includes(searchTerm) ||
        description.includes(searchTerm) ||
        category.includes(searchTerm);
}

function foodItemMatchesCategory(item, category) {
    if (!category) {
        return false;
    }
    if (category === 'all') {
        return true;
    }
    if (category === 'favorites') {
        return item.getAttribute('data-favorite') === 'true';
    }
    return item.getAttribute('data-category') === category;
}

function favoriteUrlForRecipe(recipeId) {
    const cfg = window.LOG_FEEDING_CONFIG || {};
    const template = cfg.favoriteUrlTemplate || '/api/recipes/0/favorite';
    return template.replace('/0/', '/' + encodeURIComponent(recipeId) + '/');
}

function updateFavoriteUi(foodItem, isFavorite) {
    const favoriteValue = isFavorite ? 'true' : 'false';
    foodItem.setAttribute('data-favorite', favoriteValue);
    const starBtn = foodItem.querySelector('.food-favorite-btn');
    if (starBtn) {
        starBtn.setAttribute('data-favorite', favoriteValue);
        starBtn.title = isFavorite ? 'Remove from favorites' : 'Add to favorites';
        starBtn.setAttribute('aria-label', starBtn.title);
        const icon = starBtn.querySelector('i');
        if (icon) {
            icon.className = isFavorite ? 'fas fa-star' : 'fas fa-star-o';
        }
    }
    const cardBtn = foodItem.querySelector('.quick-food-btn');
    if (cardBtn) {
        cardBtn.classList.toggle('food-card--favorite', isFavorite);
    }
}

function updateFavoritesTabCount() {
    const favoritesTab = document.getElementById('favorites-tab');
    if (!favoritesTab) {
        return;
    }
    const count = document.querySelectorAll('.food-item[data-favorite="true"]').length;
    favoritesTab.innerHTML = '<i class="fas fa-star text-warning"></i> Favorites (' + count + ')';
}

function reorderFoodItemsByFavorite() {
    const foodsGrid = document.getElementById('foodsGrid');
    if (!foodsGrid) {
        return;
    }
    const items = Array.from(foodsGrid.querySelectorAll('.food-item'));
    items.sort(function(a, b) {
        const aFav = a.getAttribute('data-favorite') === 'true' ? 0 : 1;
        const bFav = b.getAttribute('data-favorite') === 'true' ? 0 : 1;
        if (aFav !== bFav) {
            return aFav - bFav;
        }
        return (a.getAttribute('data-name') || '').localeCompare(b.getAttribute('data-name') || '');
    });
    items.forEach(function(item) {
        foodsGrid.appendChild(item);
    });
}

function toggleFoodFavorite(event, btn) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const recipeId = btn.getAttribute('data-recipe-id');
    if (!recipeId) {
        return false;
    }
    fetch(favoriteUrlForRecipe(recipeId), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (!result.ok || !result.data.success) {
            alert('Could not update favorite: ' + (result.data.message || 'Unknown error'));
            return;
        }
        const foodItem = btn.closest('.food-item');
        if (foodItem) {
            updateFavoriteUi(foodItem, result.data.is_favorite);
            reorderFoodItemsByFavorite();
            updateFavoritesTabCount();
            if (currentCategory) {
                applyFoodFilters();
            }
        }
    })
    .catch(function(error) {
        console.error('Error toggling favorite:', error);
        alert('Failed to update favorite. Please try again.');
    });
    return false;
}

function applyFoodFilters() {
    const searchInput = document.getElementById('foodSearch');
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const isSearching = searchTerm.length > 0;
    const foodItems = document.querySelectorAll('.food-item');
    let visibleCount = 0;

    foodItems.forEach(function(item) {
        const matchesSearch = !isSearching || foodItemMatchesSearch(item, searchTerm);
        let matchesCategory;
        if (isSearching && !currentCategory) {
            matchesCategory = true;
        } else {
            matchesCategory = foodItemMatchesCategory(item, currentCategory);
        }
        if (matchesSearch && matchesCategory) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    const noResults = document.getElementById('noResults');
    const foodsGrid = document.getElementById('foodsGrid');
    if (noResults) {
        if (visibleCount === 0) {
            if (!currentCategory && !isSearching) {
                noResults.style.display = 'none';
            } else {
                noResults.style.display = 'block';
            }
        } else {
            noResults.style.display = 'none';
        }
    }
    if (foodsGrid) {
        foodsGrid.style.display = (visibleCount === 0 && (currentCategory || isSearching)) ? 'none' : '';
    }
}

function searchFoods() {
    applyFoodFilters();
}

function clearSearch() {
    const searchInput = document.getElementById('foodSearch');
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    applyFoodFilters();
}

// Collapse food grid and clear category selection
function hideFoodGrid() {
    currentCategory = '';
    document.querySelectorAll('#categoryTabs .nav-link').forEach(function(navLink) {
        navLink.classList.remove('active');
        navLink.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.food-item').forEach(function(item) {
        item.classList.add('hidden');
    });
    const noResults = document.getElementById('noResults');
    if (noResults) {
        noResults.style.display = 'none';
    }
    const foodsGrid = document.getElementById('foodsGrid');
    if (foodsGrid) {
        foodsGrid.style.display = '';
    }
}

// Category filtering (click the active tab again to collapse)
function filterByCategory(category, clickedElement) {
    const clickedTab = clickedElement ? clickedElement.closest('.nav-link') : null;
    if (clickedTab && clickedTab.classList.contains('active') && currentCategory === category) {
        hideFoodGrid();
        return;
    }

    currentCategory = category;

    document.querySelectorAll('#categoryTabs .nav-link').forEach(function(navLink) {
        navLink.classList.remove('active');
        navLink.setAttribute('aria-selected', 'false');
    });

    if (clickedTab) {
        clickedTab.classList.add('active');
        clickedTab.setAttribute('aria-selected', 'true');
    } else if (category === 'all') {
        const allTab = document.getElementById('all-tab');
        if (allTab) {
            allTab.classList.add('active');
            allTab.setAttribute('aria-selected', 'true');
        }
    }

    applyFoodFilters();
}
