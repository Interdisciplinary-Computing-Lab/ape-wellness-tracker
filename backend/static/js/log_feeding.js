let selectedApes = new Set();
let feedingItems = [];
let saveFeedingInProgress = false;
let feedingSaveSuccessTimer = null;
let currentCategory = ''; // Start with no category selected (hide all foods until clicked)
const FN = window.FeedingNutrition;

// Helper function to format quantity to avoid floating point precision issues
function formatQuantity(qty) {
    return FN.formatQuantity(qty);
}

function normalizeUnit(unit) { return FN.normalizeUnit(unit); }
function convertUnit(quantity, fromUnit, toUnit) { return FN.convertUnit(quantity, fromUnit, toUnit); }
function getUnitCategory(unit) { return FN.getUnitCategory(unit); }
function canConvertUnits(fromUnit, toUnit) { return FN.canConvertUnits(fromUnit, toUnit); }
const ALL_FEEDING_UNITS = FN.ALL_FEEDING_UNITS;

function recalculateItemCalories(item) {
    return FN.recalculateItem(item);
}

function showNoApesWarning() {
    const el = document.getElementById('noApesSelected');
    if (el) {
        el.style.display = 'block';
    }
}

function hideNoApesWarning() {
    const el = document.getElementById('noApesSelected');
    if (el) {
        el.style.display = 'none';
    }
}

function requireApeBeforeAddingFood() {
    if (selectedApes.size > 0) {
        return true;
    }
    showNoApesWarning();
    return false;
}

function stepCustomQuantity(delta, stepSize) {
    stepSize = stepSize > 0 ? stepSize : 1;
    const input = document.getElementById('customQuantity');
    if (!input) return;
    const current = parseFloat(input.value) || 1;
    const minQty = stepSize < 1 ? 0.01 : 1;
    let next = current + delta * stepSize;
    next = Math.round(next * 1000) / 1000;
    next = Math.max(minQty, next);
    input.value = formatQuantity(next);
}

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

document.addEventListener('DOMContentLoaded', function() {
    updateSelectedCount();
    updateStats();
    updateSaveButton();
    
    // Hide all food items initially - user must click "All" or a category to see foods
    hideFoodGrid();

    document.querySelectorAll('#categoryTabs .nav-link').forEach(function(link) {
        const existing = link.getAttribute('title');
        link.setAttribute('title', existing ? existing + ' — click again to hide' : 'Click again to hide foods');
    });

    const foodSearchInput = document.getElementById('foodSearch');
    if (foodSearchInput) {
        foodSearchInput.addEventListener('input', applyFoodFilters);
        foodSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                clearSearch();
            }
        });
    }
    
    // Default feeding date from server (matches dashboard "Meals Today")
    var cfg = window.LOG_FEEDING_CONFIG || {};
    const feedingDateEl = document.getElementById('feedingDate');
    if (feedingDateEl && cfg.defaultFeedingDate && !feedingDateEl.value) {
        feedingDateEl.value = cfg.defaultFeedingDate;
    }
    
    if (cfg.preFilledFood) {
        var customFoodNameEl = document.getElementById('customFoodName');
        if (customFoodNameEl) {
            customFoodNameEl.value = cfg.preFilledFood;
        }
    }
    if (cfg.preFilledCalories) {
        var customCaloriesEl = document.getElementById('customCalories');
        if (customCaloriesEl) {
            customCaloriesEl.value = cfg.preFilledCalories;
        }
    }
    if (cfg.preFilledApe) {
        var apeId = parseInt(cfg.preFilledApe, 10);
        if (apeId) {
            var apeElement = document.querySelector('[data-ape-id="' + apeId + '"]');
            if (apeElement) {
                toggleApeSelection(apeElement, apeId);
            }
        }
    }
    
    // Ensure all food buttons are clickable (inline onclick handlers are primary)
    const foodButtons = document.querySelectorAll('.quick-food-btn');
    foodButtons.forEach(function(btn) {
        // Force clickable styles
        btn.style.cursor = 'pointer';
        btn.style.pointerEvents = 'auto';
        btn.style.zIndex = '100';
        btn.style.position = 'relative';
        // Remove any disabled attribute
        btn.disabled = false;
        btn.setAttribute('tabindex', '0');
        
        // onclick on the button is the only handler (a duplicate listener caused qty=2)
        if (!btn.getAttribute('onclick')) {
            btn.setAttribute('onclick', 'addFoodFromButton(this); return false;');
        }
    });
    // Ensure save button is clickable (onclick only — duplicate listeners broke save spinner)
    const saveBtn = document.getElementById('saveFeedingBtn');
    if (saveBtn) {
        saveBtn.style.pointerEvents = 'auto';
        saveBtn.style.cursor = 'pointer';
        saveBtn.style.zIndex = '100';
        saveBtn.style.position = 'relative';
    }
    
    initFeedingSummaryListeners();

    const customFoodForm = document.getElementById('customFoodForm');
    if (customFoodForm) {
        customFoodForm.addEventListener('click', function(e) {
            const stepBtn = e.target.closest('[data-custom-qty-step]');
            if (!stepBtn) return;
            e.preventDefault();
            const delta = parseInt(stepBtn.getAttribute('data-custom-qty-step'), 10);
            const stepSize = parseFloat(stepBtn.getAttribute('data-custom-qty-step-size') || '1');
            if (!isNaN(delta)) {
                stepCustomQuantity(delta, stepSize);
            }
        });
    }
});

function initFeedingSummaryListeners() {
    const feedingSummaryBody = document.getElementById('feedingSummaryBody');
    if (!feedingSummaryBody || feedingSummaryBody.dataset.listenersBound === '1') {
        return;
    }
    feedingSummaryBody.dataset.listenersBound = '1';

    feedingSummaryBody.addEventListener('input', function(e) {
        const calInput = e.target.closest('input[data-calories-input]');
        if (calInput) {
            const index = parseInt(calInput.dataset.index, 10);
            const item = feedingItems[index];
            if (!item || !item.manualCalories) return;
            const v = parseInt(calInput.value, 10);
            if (isNaN(v) || v < 0) return;
            item.caloriesOverride = v;
            recalculateItemCalories(item);
            syncRowFromItem(index, false);
            return;
        }
        const qtyInput = e.target.closest('input[data-feeding-qty]');
        if (!qtyInput) return;
        const index = parseInt(qtyInput.dataset.index, 10);
        if (isNaN(index) || index < 0 || index >= feedingItems.length) return;
        const newQty = parseFloat(qtyInput.value);
        if (!isNaN(newQty) && newQty > 0) {
            applyQuantityChange(index, newQty, false);
        }
    });

    feedingSummaryBody.addEventListener('click', function(e) {
        const stepBtn = e.target.closest('button[data-qty-step]');
        if (!stepBtn) return;
        e.preventDefault();
        const index = parseInt(stepBtn.dataset.index, 10);
        const delta = parseInt(stepBtn.getAttribute('data-qty-step'), 10);
        const stepSize = parseFloat(stepBtn.getAttribute('data-qty-step-size') || '1');
        if (!isNaN(index) && !isNaN(delta) && !isNaN(stepSize)) {
            applyQuantityStep(index, delta, stepSize);
        }
    });

    feedingSummaryBody.addEventListener('change', function(e) {
        const unitSelect = e.target.closest('select[data-feeding-unit]');
        if (unitSelect) {
            const index = parseInt(unitSelect.dataset.index, 10);
            if (!isNaN(index) && index >= 0 && index < feedingItems.length) {
                applyUnitChange(index, unitSelect.value);
            }
            return;
        }
        const qtyInput = e.target.closest('input[data-feeding-qty]');
        if (qtyInput) {
            const index = parseInt(qtyInput.dataset.index, 10);
            if (isNaN(index) || index < 0 || index >= feedingItems.length) return;
            const newQty = parseFloat(qtyInput.value);
            if (isNaN(newQty) || newQty <= 0) {
                qtyInput.value = formatQuantity(feedingItems[index].quantity || 1.0);
                applyQuantityChange(index, feedingItems[index].quantity || 1.0, true);
            } else {
                applyQuantityChange(index, newQty, true);
            }
        }
    });
}

// Ape selection functions
function toggleApeSelection(element, apeId) {
    const id = parseInt(apeId);
    if (selectedApes.has(id)) {
        selectedApes.delete(id);
        element.classList.remove('selected');
    } else {
        selectedApes.add(id);
        element.classList.add('selected');
    }
    if (selectedApes.size > 0) {
        hideNoApesWarning();
    }
    updateSelectedCount();
    updateSaveButton();
    updateStats();
}

function selectAllApes() {
    selectedApes.clear();
    document.querySelectorAll('.ape-avatar').forEach(function(element) {
        const apeId = parseInt(element.getAttribute('data-ape-id'));
        selectedApes.add(apeId);
        element.classList.add('selected');
    });
    hideNoApesWarning();
    updateSelectedCount();
    updateSaveButton();
    updateStats();
}

function clearSelection() {
    selectedApes.clear();
    document.querySelectorAll('.ape-avatar').forEach(function(element) {
        element.classList.remove('selected');
    });
    updateSelectedCount();
    updateSaveButton();
    updateStats();
}

function updateSelectedCount() {
    const selectedCountEl = document.getElementById('selectedCount');
    if (selectedCountEl) {
        selectedCountEl.textContent = selectedApes.size;
    }
}

function updateStats() {
    // Stats display removed - function kept for compatibility
    // This prevents JavaScript errors when stats elements don't exist
}

function updateSaveButton() {
    const saveBtn = document.getElementById('saveFeedingBtn');
    if (!saveBtn) {
        return;
    }
    saveBtn.disabled = selectedApes.size === 0 || feedingItems.length === 0;
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
    return item.getAttribute('data-category') === category;
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

// Food management functions
function addCustomFood() {
    if (!requireApeBeforeAddingFood()) {
        return;
    }

    const name = document.getElementById('customFoodName').value.trim();
    const quantity = parseFloat(document.getElementById('customQuantity').value) || 1.0;
    const unitSelect = document.getElementById('customUnit');
    const unit = unitSelect.options[unitSelect.selectedIndex].value.trim();
    const calories = parseInt(document.getElementById('customCalories').value);
    
    if (!name || !calories) {
        alert('Please enter food name and calories');
        return;
    }
    
    if (isNaN(quantity) || quantity <= 0) {
        alert('Please enter a valid quantity (must be greater than 0)');
        return;
    }
    
    // Normalize unit
    const normalizedUnit = normalizeUnit(unit);
    
    // For custom foods, the user enters total calories for the quantity they want to log
    // We'll treat this as: base quantity = 1.0, base calories = calories/quantity
    // This way, 1.0 unit = (calories/quantity) calories
    const catalogCalories = calories;
    const existingIndex = feedingItems.findIndex(function(item) { return item.name === name; });
    if (existingIndex !== -1) {
        feedingItems[existingIndex].quantity = quantity;
        feedingItems[existingIndex].unit = normalizedUnit;
        recalculateItemCalories(feedingItems[existingIndex]);
    } else {
        const item = FN.buildFeedingItem({
            name: name,
            calories: catalogCalories,
            recipeQuantity: quantity,
            unitRaw: unit,
            source: '',
        });
        item.quantity = quantity;
        item.unit = normalizedUnit;
        recalculateItemCalories(item);
        feedingItems.push(item);
    }
    
    // Clear form
    document.getElementById('customFoodName').value = '';
    document.getElementById('customQuantity').value = '1';
    document.getElementById('customUnit').selectedIndex = 0; // Reset to "piece"
    document.getElementById('customCalories').value = '';
    
    updateFeedingSummary();
    updateSaveButton();
    updateStats();
}

function addFoodItem(name, calories, recipeQuantity, unitRaw, source, gramsPerServing) {
    recipeQuantity = recipeQuantity || 1.0;
    const existingIndex = feedingItems.findIndex(function(item) { return item.name === name; });
    if (existingIndex !== -1) {
        feedingItems[existingIndex].quantity += FN.catalogServingIncrement(feedingItems[existingIndex]);
        recalculateItemCalories(feedingItems[existingIndex]);
    } else {
        const item = FN.buildFeedingItem({
            name: name,
            calories: calories,
            recipeQuantity: recipeQuantity,
            unitRaw: unitRaw || '',
            source: source || '',
            gramsPerServing: gramsPerServing || 0,
        });
        recalculateItemCalories(item);
        feedingItems.push(item);
    }
    updateFeedingSummary();
    updateSaveButton();
    updateStats();
}

function updateFeedingTotalsInDom() {
    let totalCal = 0;
    feedingItems.forEach(function(itm) {
        if (!itm.caloriesInvalid && itm.totalCalories != null) {
            totalCal += itm.totalCalories;
        }
    });
    const totalCalEl = document.getElementById('totalCalories');
    if (totalCalEl) {
        totalCalEl.textContent = Math.round(totalCal);
    }
}

function catalogServingHint(item) {
    if (item.foodSpecificServing) {
        return formatQuantity(item.recipeQuantity) + ' ' + (item.servingLabel || 'serving');
    }
    return formatQuantity(item.recipeQuantity) + ' ' + (item.catalogUnit || 'serving');
}

function toggleManualCalories(index) {
    const item = feedingItems[index];
    if (!item) return;
    item.manualCalories = !item.manualCalories;
    if (item.manualCalories) {
        item.caloriesOverride = item.totalCalories != null ? item.totalCalories : item.calories;
    } else {
        item.caloriesOverride = null;
    }
    updateFeedingSummary();
}

function syncCaloriesCellFromItem(calCell, item, flash) {
    if (!calCell || !item) return;
    const calInput = calCell.querySelector('input[data-calories-input]');
    const lockBtn = calCell.querySelector('button[data-calories-lock]');
    if (!calInput) return;

    if (item.caloriesInvalid) {
        calInput.value = '';
        calInput.disabled = true;
        calCell.classList.add('calories-invalid');
        calCell.title = 'Cannot convert ' + (item.unit || '') + ' for this food (USDA basis: ' + catalogServingHint(item) + '). Try a weight unit (g, oz, lb) or the catalog serving.';
        return;
    }

    calCell.classList.remove('calories-invalid');
    calInput.disabled = !item.manualCalories;
    calInput.value = Math.round(item.totalCalories || 0);
    if (lockBtn) {
        lockBtn.className = 'btn btn-sm ' + (item.manualCalories ? 'btn-warning' : 'btn-outline-secondary');
        lockBtn.title = item.manualCalories ? 'Manual override (click for auto)' : 'Override calories';
    }
    let hint = 'Auto from USDA catalog: ' + catalogServingHint(item);
    if (item.approximateCalories) hint += ' (estimated conversion)';
    calCell.title = hint;

    if (flash) {
        calCell.classList.add('calories-updated');
        setTimeout(function() { calCell.classList.remove('calories-updated'); }, 400);
    }
}

function syncRowFromItem(index, flash) {
    const item = feedingItems[index];
    if (!item) return;

    recalculateItemCalories(item);

    const tbody = document.getElementById('feedingSummaryBody');
    if (!tbody) return;
    const row = tbody.querySelectorAll('tr')[index];
    if (!row) return;

    syncCaloriesCellFromItem(row.querySelector('td.calories-cell'), item, flash);

    const qtyInput = row.querySelector('input[data-feeding-qty]');
    if (qtyInput) {
        qtyInput.value = formatQuantity(item.quantity);
    }
    const unitSelect = row.querySelector('select[data-feeding-unit]');
    if (unitSelect && unitSelect.value !== item.unit) {
        unitSelect.value = item.unit;
    }

    updateFeedingTotalsInDom();
    updateSaveButton();
    updateStats();
}

function applyQuantityChange(index, newQuantity, flash) {
    if (index < 0 || index >= feedingItems.length) return;
    if (isNaN(newQuantity) || newQuantity <= 0) return;

    feedingItems[index].quantity = newQuantity;
    syncRowFromItem(index, flash);
}

function applyQuantityStep(index, delta, stepSize) {
    if (index < 0 || index >= feedingItems.length) return;
    stepSize = stepSize > 0 ? stepSize : 1;
    const item = feedingItems[index];
    const current = item.quantity > 0 ? item.quantity : 1;
    const minQty = stepSize < 1 ? 0.01 : 1;
    let next = current + delta * stepSize;
    next = Math.round(next * 1000) / 1000;
    next = Math.max(minQty, next);
    applyQuantityChange(index, next, true);
}

function createQtyStepper(index, stepSize) {
    const stepper = document.createElement('div');
    stepper.className =
        'btn-group-vertical feeding-qty-stepper btn-group-sm' +
        (stepSize < 1 ? ' feeding-qty-stepper--fine' : '');

    const upBtn = document.createElement('button');
    upBtn.type = 'button';
    upBtn.className = 'btn btn-outline-secondary';
    upBtn.setAttribute('data-qty-step', '1');
    upBtn.setAttribute('data-qty-step-size', String(stepSize));
    upBtn.dataset.index = index;
    upBtn.title = stepSize < 1 ? 'Add 0.1' : 'Add 1';
    upBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';

    const downBtn = document.createElement('button');
    downBtn.type = 'button';
    downBtn.className = 'btn btn-outline-secondary';
    downBtn.setAttribute('data-qty-step', '-1');
    downBtn.setAttribute('data-qty-step-size', String(stepSize));
    downBtn.dataset.index = index;
    downBtn.title = stepSize < 1 ? 'Subtract 0.1' : 'Subtract 1';
    downBtn.innerHTML = '<i class="fas fa-chevron-down"></i>';

    stepper.appendChild(upBtn);
    stepper.appendChild(downBtn);
    return stepper;
}

function createQtyControl(index, item) {
    if (!item.quantity || item.quantity <= 0) {
        item.quantity = 1.0;
    }
    const wrap = document.createElement('div');
    wrap.className = 'feeding-qty-control d-flex align-items-center';

    const qtyInput = document.createElement('input');
    qtyInput.type = 'number';
    qtyInput.className = 'form-control form-control-sm';
    qtyInput.value = formatQuantity(item.quantity);
    qtyInput.step = 'any';
    qtyInput.min = '0.01';
    qtyInput.dataset.index = index;
    qtyInput.setAttribute('data-feeding-qty', '1');

    const steppers = document.createElement('div');
    steppers.className = 'd-flex feeding-qty-steppers';
    steppers.appendChild(createQtyStepper(index, 1));
    steppers.appendChild(createQtyStepper(index, 0.1));

    wrap.appendChild(qtyInput);
    wrap.appendChild(steppers);
    return wrap;
}

function applyUnitChange(index, newUnit) {
    if (index < 0 || index >= feedingItems.length) return;

    const item = feedingItems[index];
    item.unit = normalizeUnit(newUnit);
    if (!item.manualCalories) {
        item.caloriesOverride = null;
    }
    syncRowFromItem(index, true);
}

function updateFeedingSummary() {
    const tbody = document.getElementById('feedingSummaryBody');
    tbody.innerHTML = '';
    
    let totalCalories = 0;

    feedingItems.forEach(function(item, index) {
        const row = document.createElement('tr');
        // Create unit select
        const unitSelect = document.createElement('select');
        unitSelect.className = 'form-control form-control-sm';
        unitSelect.style.width = '120px';
        unitSelect.style.pointerEvents = 'auto';
        unitSelect.style.zIndex = '10';
        unitSelect.dataset.index = index;
        unitSelect.setAttribute('data-feeding-unit', '1');
        unitSelect.disabled = false;
        const baseUnit = item.catalogUnit || 'serving';
        unitSelect.title = 'Catalog serving: ' + catalogServingHint(item) + '. Change unit within the same type (g/oz, cup/tbsp, serving/piece).';

        const selectedUnit = normalizeUnit(item.unit || baseUnit);
        const allowedUnits = FN.unitsForItem(item);
        allowedUnits.forEach(function(opt) {
            const option = document.createElement('option');
            option.value = opt;
            option.textContent = opt;
            if (opt === selectedUnit) {
                option.selected = true;
            }
            unitSelect.appendChild(option);
        });
        if (selectedUnit && allowedUnits.indexOf(selectedUnit) === -1) {
            const option = document.createElement('option');
            option.value = selectedUnit;
            option.textContent = selectedUnit;
            option.selected = true;
            unitSelect.appendChild(option);
        }
        item.unit = selectedUnit;

        recalculateItemCalories(item);

        const nameCell = document.createElement('td');
        nameCell.title = item.name;
        nameCell.textContent = item.name.length > 18 ? item.name.substr(0, 18) + '…' : item.name;

        const qtyCell = document.createElement('td');
        qtyCell.appendChild(createQtyControl(index, item));

        const unitCell = document.createElement('td');
        unitCell.appendChild(unitSelect);

        const calCell = document.createElement('td');
        calCell.className = 'calories-cell' + (item.caloriesInvalid ? ' calories-invalid' : '');
        const calWrap = document.createElement('div');
        calWrap.className = 'd-flex align-items-center';
        const calInput = document.createElement('input');
        calInput.type = 'number';
        calInput.className = 'form-control form-control-sm';
        calInput.style.width = '62px';
        calInput.min = '0';
        calInput.dataset.index = index;
        calInput.setAttribute('data-calories-input', '1');
        calInput.disabled = !item.manualCalories;
        calInput.value = item.caloriesInvalid ? '' : Math.round(item.totalCalories || 0);
        const lockBtn = document.createElement('button');
        lockBtn.type = 'button';
        lockBtn.className = 'btn btn-sm ml-1 ' + (item.manualCalories ? 'btn-warning' : 'btn-outline-secondary');
        lockBtn.setAttribute('data-calories-lock', '1');
        lockBtn.title = item.manualCalories ? 'Manual override' : 'Auto-calculate';
        lockBtn.innerHTML = '<i class="fas fa-' + (item.manualCalories ? 'pen' : 'magic') + '"></i>';
        lockBtn.addEventListener('click', function() { toggleManualCalories(index); });
        calWrap.appendChild(calInput);
        calWrap.appendChild(lockBtn);
        calCell.appendChild(calWrap);
        syncCaloriesCellFromItem(calCell, item, false);

        const actionCell = document.createElement('td');
        actionCell.innerHTML = '<button type="button" class="btn btn-sm btn-outline-danger" title="Remove"><i class="fas fa-times"></i></button>';
        actionCell.querySelector('button').addEventListener('click', function() { removeFoodItem(index); });

        row.appendChild(nameCell);
        row.appendChild(qtyCell);
        row.appendChild(unitCell);
        row.appendChild(calCell);
        row.appendChild(actionCell);
        tbody.appendChild(row);
        if (!item.caloriesInvalid && item.totalCalories != null) {
            totalCalories += item.totalCalories;
        }
    });

    updateFeedingTotalsInDom();
    initFeedingSummaryListeners();
}

// Backward-compatible aliases (if referenced elsewhere)
function updateItemQuantity(index, newQuantity) {
    applyQuantityChange(index, newQuantity, true);
}

function updateItemUnit(index, newUnit) {
    applyUnitChange(index, newUnit);
}

function removeFoodItem(index) {
    feedingItems.splice(index, 1);
    updateFeedingSummary();
    updateSaveButton();
    updateStats();
}

function clearFeedingList() {
    feedingItems = [];
    updateFeedingSummary();
    updateSaveButton();
    updateStats();
}

function resetFeedingSession() {
    if (!confirm(
        'Reset this session?\n\nThis will clear selected apes, all foods in the list, and your search.'
    )) {
        return;
    }
    clearAll();
}

function clearAll() {
    // Set flag to prevent showing warning during clear
    window.isClearingAfterSave = true;

    clearSelection();
    clearFeedingList();
    clearSearch();
    hideFoodGrid();

    // Reset flag after a short delay to allow the clear operations to complete
    setTimeout(() => {
        window.isClearingAfterSave = false;
    }, 100);
}

function formatSavedCalories(value) {
    const n = Number(value);
    if (!isFinite(n)) {
        return '0';
    }
    return n.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 1
    });
}

function hideFeedingSaveSuccess() {
    const el = document.getElementById('feedingSaveSuccess');
    if (!el) {
        return;
    }
    el.classList.remove('is-visible');
    el.classList.add('is-hiding', 'd-none');
}

function showFeedingSaveSuccess(apeCount, totalCalories, mealCount) {
    const el = document.getElementById('feedingSaveSuccess');
    const textEl = document.getElementById('feedingSaveSuccessText');
    if (!el || !textEl) {
        return;
    }
    if (feedingSaveSuccessTimer) {
        clearTimeout(feedingSaveSuccessTimer);
        feedingSaveSuccessTimer = null;
    }
    const apes = Number(apeCount) || 0;
    const cals = formatSavedCalories(totalCalories);
    const meals = Number(mealCount) || 0;
    const apeLabel = apes === 1 ? '1 ape' : apes + ' apes';
    const mealLabel = meals === 1 ? '1 meal' : meals + ' meals';
    textEl.innerHTML =
        'Meals logged for <strong>' + apeLabel + '</strong> (' + mealLabel + ') — ' +
        '<span id="feedingSaveSuccessCal">' + cals + ' cal</span>';
    el.classList.remove('d-none', 'is-hiding');
    el.classList.add('is-visible');
    feedingSaveSuccessTimer = setTimeout(function() {
        el.classList.add('is-hiding');
        feedingSaveSuccessTimer = setTimeout(function() {
            hideFeedingSaveSuccess();
            feedingSaveSuccessTimer = null;
        }, 400);
    }, 4500);
}

// Save meals function - must be global for inline onclick
function saveFeeding() {
    if (saveFeedingInProgress) {
        return;
    }
    if (selectedApes.size === 0 || feedingItems.length === 0) {
        return;
    }

    feedingItems.forEach(function(item) {
        recalculateItemCalories(item);
    });
    const invalidItems = feedingItems.filter(function(item) {
        return item.caloriesInvalid;
    });
    if (invalidItems.length > 0) {
        alert(
            'Some items have a unit that does not match how that food is stored (for example per piece vs per cup vs per 100g). '
            + 'Rows marked "—" in Calories must be fixed before saving. Update the unit, or edit the food in Manage Foods.'
        );
        updateFeedingSummary();
        return;
    }

    const saveBtn = document.getElementById('saveFeedingBtn');
    if (!saveBtn) {
        return;
    }
    const originalText = saveBtn.innerHTML;
    saveFeedingInProgress = true;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Saving...';
    saveBtn.disabled = true;
    
    // Prepare data for server
    // Transform feedingItems to match backend expectations
    // Backend expects: {name, calories, quantity}
    // We have: {name, calories, recipeQuantity, caloriesPerUnit, quantity, unit, source, totalCalories}
    // 
    // The backend multiplies: calories * quantity
    // So if recipe has: calories=100 for quantity=1.0 (1 cup), and user consumed 0.5 cups:
    // We should send: calories=100, quantity=0.5
    // Backend calculates: 100 * 0.5 = 50 calories
    //
    // But wait, the backend's quantity is a multiplier, not the actual quantity.
    // If recipe quantity=1.0 and user consumed 0.5, then multiplier = 0.5/1.0 = 0.5
    // So we send: calories=100, quantity=0.5
    const transformedItems = feedingItems.map(function(item) {
        recalculateItemCalories(item);
        return {
            name: item.name,
            calories: Math.round(item.totalCalories || 0),
            quantity: 1.0,
            unit: item.unit || '',
            source: item.source || ''
        };
    });
    
    const dateEl = document.getElementById('feedingDate');
    const periodEl = document.getElementById('feedingPeriod');
    // Get date in local timezone format (YYYY-MM-DD)
    let dateValue = '';
    if (dateEl && dateEl.value) {
        dateValue = dateEl.value;
    } else {
        // Fallback to today in local timezone
        const today = new Date();
        dateValue = today.getFullYear() + '-' + 
                    String(today.getMonth() + 1).padStart(2, '0') + '-' + 
                    String(today.getDate()).padStart(2, '0');
    }
    const feedingData = {
        ape_ids: Array.from(selectedApes),
        feeding_items: transformedItems,
        date: dateValue,
        feeding_period: periodEl ? periodEl.value : 'morning'
    };
    
    // Send data to server
    fetch((window.LOG_FEEDING_CONFIG && window.LOG_FEEDING_CONFIG.saveUrl) || '/save_feeding', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(feedingData),
        credentials: 'same-origin'
    })
    .then(function(response) {
        return response.json().then(function(data) {
            return { ok: response.ok, data: data };
        });
    })
    .then(function(result) {
        if (result.ok && result.data.success) {
            showFeedingSaveSuccess(
                result.data.ape_count,
                result.data.total_calories,
                result.data.meal_count
            );
            clearAll();
        } else {
            alert('Error saving meals: ' + (result.data.error || 'Unknown error'));
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
        alert('Failed to save meals. Please try again.');
    })
    .finally(function() {
        saveFeedingInProgress = false;
        saveBtn.innerHTML = originalText;
        updateSaveButton();
    });
}

// Handle custom food modal (fallback for cases where it's not defined)
function showCustomFoodModal() {
    // Scroll to custom food form
    const customForm = document.getElementById('customFoodForm');
    if (customForm) {
        customForm.scrollIntoView({ behavior: 'smooth' });
        document.getElementById('customFoodName').focus();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        saveFeeding();
    }
    // Ctrl/Cmd + A to select all apes
    if ((e.ctrlKey || e.metaKey) && e.key === 'a') {
        e.preventDefault();
        selectAllApes();
    }
    // Ctrl/Cmd + C to reset session
    if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
        e.preventDefault();
        resetFeedingSession();
    }
    // Ctrl/Cmd + F to focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault();
        document.getElementById('foodSearch').focus();
    }
});

// Type-to-search: focus food search and append the key (when not already in a field)
document.addEventListener('keydown', function(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) {
        return;
    }
    if (e.key.length !== 1 || !/^[a-zA-Z0-9]$/.test(e.key)) {
        return;
    }
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
        return;
    }
    const checkoutTable = document.getElementById('feedingSummaryTable');
    if (checkoutTable && checkoutTable.contains(e.target)) {
        return;
    }
    const searchInput = document.getElementById('foodSearch');
    if (!searchInput || document.activeElement === searchInput) {
        return;
    }
    e.preventDefault();
    searchInput.focus();
    searchInput.value = searchInput.value + e.key;
    applyFoodFilters();
});

// Date quick selection functions
function setDateToYesterday() {
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    const dateStr = yesterday.getFullYear() + '-' + 
                    String(yesterday.getMonth() + 1).padStart(2, '0') + '-' + 
                    String(yesterday.getDate()).padStart(2, '0');
    const feedingDateEl = document.getElementById('feedingDate');
    const feedingDateSummaryEl = document.getElementById('feedingDateSummary');
    if (feedingDateEl) feedingDateEl.value = dateStr;
    if (feedingDateSummaryEl) feedingDateSummaryEl.value = dateStr;
}

function setDateToToday() {
    const cfg = window.LOG_FEEDING_CONFIG || {};
    const todayStr = cfg.defaultFeedingDate || formatLocalDate(new Date());
    const feedingDateEl = document.getElementById('feedingDate');
    const feedingDateSummaryEl = document.getElementById('feedingDateSummary');
    if (feedingDateEl) feedingDateEl.value = todayStr;
    if (feedingDateSummaryEl) feedingDateSummaryEl.value = todayStr;
}

function formatLocalDate(d) {
    return d.getFullYear() + '-' +
        String(d.getMonth() + 1).padStart(2, '0') + '-' +
        String(d.getDate()).padStart(2, '0');
}

function setDateToTomorrow() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateStr = tomorrow.getFullYear() + '-' + 
                    String(tomorrow.getMonth() + 1).padStart(2, '0') + '-' + 
                    String(tomorrow.getDate()).padStart(2, '0');
    const feedingDateEl = document.getElementById('feedingDate');
    const feedingDateSummaryEl = document.getElementById('feedingDateSummary');
    if (feedingDateEl) feedingDateEl.value = dateStr;
    if (feedingDateSummaryEl) feedingDateSummaryEl.value = dateStr;
}

window.clearFeedingList = clearFeedingList;
window.saveFeeding = saveFeeding;
