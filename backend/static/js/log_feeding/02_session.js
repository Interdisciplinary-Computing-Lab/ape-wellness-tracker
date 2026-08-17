/** @file Feeding list, summary table, and session clear. */
// Food management functions
function addCustomFood() {
    if (!requireApeBeforeAddingFood()) {
        return;
    }

    const name = document.getElementById('customFoodName').value.trim();
    const quantity = parseFloat(document.getElementById('customQuantity').value) || 1.0;
    const unitSelect = document.getElementById('customUnit');
    const unit = unitSelect.options[unitSelect.selectedIndex].value.trim();
    const calories = parseInt(document.getElementById('customCalories').value, 10);
    const proteinG = parseFloat(document.getElementById('customProtein').value) || 0;
    const fiberG = parseFloat(document.getElementById('customFiber').value) || 0;
    const notes = document.getElementById('customNotes').value.trim();
    const categoryEl = document.getElementById('customCategory');
    const foodCategory = categoryEl ? categoryEl.value.trim() : 'Other';

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

    // User enters total calories for the quantity they are logging; store that as the catalog
    // serving (calories + recipeQuantity) so quantity scaling applies without gram_weight.
    const existingIndex = feedingItems.findIndex(function(item) { return item.name === name; });
    if (existingIndex !== -1) {
        feedingItems[existingIndex].calories = calories;
        feedingItems[existingIndex].recipeQuantity = quantity;
        feedingItems[existingIndex].quantity = quantity;
        feedingItems[existingIndex].unit = normalizedUnit;
        feedingItems[existingIndex].catalogUnit = normalizedUnit;
        feedingItems[existingIndex].source = 'Custom';
        feedingItems[existingIndex].foodCategory = foodCategory;
        feedingItems[existingIndex].proteinPerCatalog = proteinG;
        feedingItems[existingIndex].fiberPerCatalog = fiberG;
        feedingItems[existingIndex].description = notes;
        recalculateItemCalories(feedingItems[existingIndex]);
    } else {
        const item = FN.buildFeedingItem({
            name: name,
            calories: calories,
            recipeQuantity: quantity,
            unitRaw: unit,
            source: 'Custom',
            proteinG: proteinG,
            fiberG: fiberG,
        });
        item.calories = calories;
        item.recipeQuantity = quantity;
        item.quantity = quantity;
        item.unit = normalizedUnit;
        item.catalogUnit = normalizedUnit;
        item.foodCategory = foodCategory;
        item.description = notes;
        recalculateItemCalories(item);
        feedingItems.push(item);
    }

    saveCustomFoodToCatalog(
        name, calories, quantity, unit, foodCategory, proteinG, fiberG, notes
    );

    // Clear form
    document.getElementById('customFoodName').value = '';
    document.getElementById('customQuantity').value = '1';
    document.getElementById('customUnit').selectedIndex = 0; // Reset to "piece"
    document.getElementById('customCalories').value = '';
    document.getElementById('customProtein').value = '';
    document.getElementById('customFiber').value = '';
    document.getElementById('customNotes').value = '';
    if (categoryEl) {
        categoryEl.selectedIndex = 0;
    }

    updateFeedingSummary();
    updateSaveButton();
    updateStats();
}

function addFoodItem(
    name, calories, recipeQuantity, unitRaw, source, gramsPerServing, proteinG, fiberG
) {
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
            proteinG: proteinG || 0,
            fiberG: fiberG || 0,
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

function enterCalorieEditMode(index) {
    const item = feedingItems[index];
    if (!item || item.caloriesInvalid) return;
    if (!item.manualCalories) {
        item.quantityBeforeCalorieEdit = item.quantity > 0 ? item.quantity : 1;
        item.manualCalories = true;
        item.caloriesOverride = item.totalCalories != null ? item.totalCalories : item.calories;
        syncRowFromItem(index, false);
    }
    const tbody = document.getElementById('feedingSummaryBody');
    const row = tbody && tbody.querySelectorAll('tr')[index];
    const calInput = row && row.querySelector('input[data-calories-input]');
    if (calInput) {
        calInput.focus();
        calInput.select();
    }
}

function resetCalorieEdit(index) {
    const item = feedingItems[index];
    if (!item) return;
    if (item.quantityBeforeCalorieEdit != null && item.quantityBeforeCalorieEdit > 0) {
        item.quantity = item.quantityBeforeCalorieEdit;
    }
    item.quantityBeforeCalorieEdit = null;
    item.manualCalories = false;
    item.caloriesOverride = null;
    syncRowFromItem(index, true);
}

function syncCaloriesCellFromItem(calCell, item, flash) {
    if (!calCell || !item) return;
    const calInput = calCell.querySelector('input[data-calories-input]');
    const wandBtn = calCell.querySelector('button[data-calories-wand]');
    const resetBtn = calCell.querySelector('button[data-calories-reset]');
    if (!calInput) return;

    if (item.caloriesInvalid) {
        calInput.value = '';
        calInput.disabled = true;
        calCell.classList.add('calories-invalid');
        if (wandBtn) wandBtn.disabled = true;
        if (resetBtn) {
            resetBtn.disabled = true;
            resetBtn.classList.add('d-none');
        }
        calCell.title = 'Cannot convert ' + (item.unit || '') + ' for this food (USDA basis: ' + catalogServingHint(item) + '). Try a weight unit (g, oz, lb) or the catalog serving.';
        return;
    }

    calCell.classList.remove('calories-invalid');
    calInput.disabled = false;
    if (document.activeElement !== calInput) {
        calInput.value = Math.round(item.totalCalories || 0);
    }
    if (wandBtn) {
        wandBtn.disabled = false;
        wandBtn.className = 'btn btn-sm ml-1 ' + (item.manualCalories ? 'btn-warning' : 'btn-outline-secondary');
        wandBtn.title = item.manualCalories ? 'Editing calories (quantity auto-adjusts)' : 'Edit calories';
        wandBtn.innerHTML = '<i class="fas fa-magic"></i>';
    }
    if (resetBtn) {
        resetBtn.disabled = !item.manualCalories;
        resetBtn.className = 'btn btn-sm ml-1 btn-warning' + (item.manualCalories ? '' : ' d-none');
        resetBtn.title = 'Reset quantity and calories';
        resetBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
    }
    let hint = 'Edit calories to auto-adjust quantity. Catalog serving: ' + catalogServingHint(item);
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
    if (qtyInput && document.activeElement !== qtyInput) {
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

    const item = feedingItems[index];
    item.quantity = newQuantity;
    item.manualCalories = false;
    item.caloriesOverride = null;
    item.quantityBeforeCalorieEdit = null;
    syncRowFromItem(index, flash);
}

function applyCaloriesChange(index, targetCalories) {
    if (index < 0 || index >= feedingItems.length) return;
    if (isNaN(targetCalories) || targetCalories < 0) return;

    const item = feedingItems[index];
    if (!item.manualCalories) {
        item.quantityBeforeCalorieEdit = item.quantity > 0 ? item.quantity : 1;
    }
    item.manualCalories = true;
    item.caloriesOverride = targetCalories;
    if (item.calories > 0) {
        let newQty = FN.quantityForTargetCalories(item, targetCalories);
        if (isNaN(newQty) || newQty <= 0) {
            const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;
            newQty = (targetCalories / item.calories) * catalogQty;
        }
        if (!isNaN(newQty) && newQty > 0) {
            item.quantity = Math.round(newQty * 1000) / 1000;
        }
    }
    syncRowFromItem(index, false);
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
    item.manualCalories = false;
    item.caloriesOverride = null;
    item.quantityBeforeCalorieEdit = null;
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
        unitSelect.className = 'form-control form-control-sm feeding-summary-unit';
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
        calInput.className = 'form-control form-control-sm feeding-summary-cal-input';
        calInput.min = '0';
        calInput.dataset.index = index;
        calInput.setAttribute('data-calories-input', '1');
        calInput.disabled = false;
        calInput.value = item.caloriesInvalid ? '' : Math.round(item.totalCalories || 0);
        const wandBtn = document.createElement('button');
        wandBtn.type = 'button';
        wandBtn.className = 'btn btn-sm ml-1 ' + (item.manualCalories ? 'btn-warning' : 'btn-outline-secondary');
        wandBtn.setAttribute('data-calories-wand', '1');
        wandBtn.title = item.manualCalories ? 'Editing calories (quantity auto-adjusts)' : 'Edit calories';
        wandBtn.innerHTML = '<i class="fas fa-magic"></i>';
        wandBtn.addEventListener('click', function() { enterCalorieEditMode(index); });
        const resetBtn = document.createElement('button');
        resetBtn.type = 'button';
        resetBtn.className = 'btn btn-sm ml-1 btn-warning' + (item.manualCalories ? '' : ' d-none');
        resetBtn.setAttribute('data-calories-reset', '1');
        resetBtn.title = 'Reset quantity and calories';
        resetBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
        resetBtn.addEventListener('click', function() { resetCalorieEdit(index); });
        calWrap.appendChild(calInput);
        calWrap.appendChild(wandBtn);
        calWrap.appendChild(resetBtn);
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
    updateStats();
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
            const v = parseInt(calInput.value, 10);
            applyCaloriesChange(index, v);
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

    feedingSummaryBody.addEventListener('focusin', function(e) {
        const calInput = e.target.closest('input[data-calories-input]');
        if (!calInput) return;
        const index = parseInt(calInput.dataset.index, 10);
        if (isNaN(index) || index < 0 || index >= feedingItems.length) return;
        const item = feedingItems[index];
        if (!item || item.caloriesInvalid || item.manualCalories) return;
        item.quantityBeforeCalorieEdit = item.quantity > 0 ? item.quantity : 1;
        item.manualCalories = true;
        item.caloriesOverride = item.totalCalories != null ? item.totalCalories : item.calories;
        const wandBtn = calInput.closest('td') && calInput.closest('td').querySelector('button[data-calories-wand]');
        const resetBtn = calInput.closest('td') && calInput.closest('td').querySelector('button[data-calories-reset]');
        if (wandBtn) {
            wandBtn.className = 'btn btn-sm ml-1 btn-warning';
            wandBtn.title = 'Editing calories (quantity auto-adjusts)';
        }
        if (resetBtn) {
            resetBtn.disabled = false;
            resetBtn.classList.remove('d-none');
            resetBtn.className = 'btn btn-sm ml-1 btn-warning';
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
        const calInput = e.target.closest('input[data-calories-input]');
        if (calInput) {
            const index = parseInt(calInput.dataset.index, 10);
            const v = parseInt(calInput.value, 10);
            if (!isNaN(v) && v >= 0) {
                applyCaloriesChange(index, v);
            } else if (index >= 0 && index < feedingItems.length) {
                calInput.value = Math.round(feedingItems[index].totalCalories || 0);
            }
            return;
        }
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

function saveCustomFoodToCatalog(
    name, calories, quantity, unit, foodCategory, proteinG, fiberG, notes
) {
    const cfg = window.LOG_FEEDING_CONFIG || {};
    const url = cfg.createRecipeUrl || '/api/recipes';
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            meal_name: name,
            calories: calories,
            quantity: quantity,
            unit_of_measurement: unit,
            food_category: foodCategory || 'Other',
            source: 'Custom',
            description: notes || '',
            protein_g: proteinG || 0,
            fiber_g: fiberG || 0
        })
    })
        .then(function(response) {
            return response.json().then(function(data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function(result) {
            if (result.data && result.data.recipe) {
                upsertCustomFoodInUi(result.data.recipe);
            }
        })
        .catch(function(error) {
            console.warn('Could not save custom food to catalog immediately:', error);
        });
}

function catalogServingLabelFromRecipe(recipe) {
    if (recipe.catalog_serving_label) {
        return recipe.catalog_serving_label;
    }
    const qty = recipe.quantity != null ? recipe.quantity : 1;
    const unit = recipe.unit_of_measurement || 'serving';
    if (qty === 1 || qty === 1.0) {
        return '1 ' + unit;
    }
    return qty + ' ' + unit;
}

function upsertCustomFoodInUi(recipe) {
    if (!recipe || !recipe.meal_name) {
        return;
    }
    const name = recipe.meal_name;
    const calories = recipe.calories;
    const quantity = recipe.quantity != null ? recipe.quantity : 1;
    const unit = recipe.unit_of_measurement || '';
    const category = recipe.food_category || 'Other';
    const recipeId = recipe.id;
    const isFavorite = !!recipe.is_favorite;
    const proteinG = recipe.protein_g || 0;
    const fiberG = recipe.fiber_g || 0;
    const servingLabel = catalogServingLabelFromRecipe(recipe);

    const grid = document.getElementById('foodsGrid');
    if (grid && recipeId) {
        let foodItem = grid.querySelector('.food-item[data-recipe-id="' + recipeId + '"]');
        if (!foodItem) {
            foodItem = Array.from(grid.querySelectorAll('.food-item')).find(function(el) {
                return (el.getAttribute('data-name') || '') === name.toLowerCase();
            }) || null;
        }
        if (!foodItem) {
            foodItem = document.createElement('div');
            foodItem.className = 'col-lg-3 col-md-4 col-sm-6 col-6 mb-2 food-item';
            foodItem.innerHTML =
                '<div class="food-card-wrap position-relative">' +
                '<button type="button" class="btn btn-link btn-sm food-favorite-btn p-0"' +
                ' data-recipe-id="" data-favorite="false" onclick="toggleFoodFavorite(event, this)"' +
                ' title="Favorite this food"><i class="fas fa-star-o"></i></button>' +
                '<span class="badge badge-secondary food-custom-badge">Custom</span>' +
                '<button type="button" class="btn btn-outline-primary w-100 h-100 py-2 quick-food-btn food-card"' +
                ' data-food="" data-calories="" data-quantity="" data-unit="" data-source="Custom"' +
                ' data-grams="0" data-protein="0" data-fiber="0" data-name="" data-category=""' +
                ' onclick="addFoodFromButton(this); return false;">' +
                '<div class="text-center">' +
                '<i class="fas fa-tag mb-1 text-secondary"></i>' +
                '<div class="d-block small font-weight-bold food-card-name"></div>' +
                '<small class="text-muted d-block food-card-serving"></small>' +
                '<small class="text-muted font-weight-bold food-card-cal"></small>' +
                '<small class="d-block text-secondary food-card-category"></small>' +
                '</div></button></div>';
            grid.appendChild(foodItem);
        }
        foodItem.setAttribute('data-recipe-id', String(recipeId));
        foodItem.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
        foodItem.setAttribute('data-custom', 'true');
        foodItem.setAttribute('data-category', category);
        foodItem.setAttribute('data-name', name.toLowerCase());
        foodItem.setAttribute('data-description', (recipe.description || '').toLowerCase());
        foodItem.setAttribute('data-calories', String(calories));

        const starBtn = foodItem.querySelector('.food-favorite-btn');
        if (starBtn) {
            starBtn.setAttribute('data-recipe-id', String(recipeId));
            starBtn.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
        }
        const cardBtn = foodItem.querySelector('.quick-food-btn');
        if (cardBtn) {
            cardBtn.setAttribute('data-food', name);
            cardBtn.setAttribute('data-name', name);
            cardBtn.setAttribute('data-calories', String(calories));
            cardBtn.setAttribute('data-quantity', String(quantity));
            cardBtn.setAttribute('data-unit', unit);
            cardBtn.setAttribute('data-source', 'Custom');
            cardBtn.setAttribute('data-category', category);
            cardBtn.setAttribute('data-protein', String(proteinG));
            cardBtn.setAttribute('data-fiber', String(fiberG));
        }
        const nameEl = foodItem.querySelector('.food-card-name');
        if (nameEl) nameEl.textContent = name;
        const servingEl = foodItem.querySelector('.food-card-serving');
        if (servingEl) servingEl.textContent = 'per ' + servingLabel;
        const calEl = foodItem.querySelector('.food-card-cal');
        if (calEl) calEl.textContent = calories + ' cal';
        const catEl = foodItem.querySelector('.food-card-category');
        if (catEl) catEl.textContent = category;
    }

    const body = document.getElementById('customFoodsBody');
    if (body) {
        const empty = document.getElementById('customFoodsEmptyRow');
        if (empty) empty.remove();
        let row = recipeId ? body.querySelector('tr[data-recipe-id="' + recipeId + '"]') : null;
        if (!row) {
            row = Array.from(body.querySelectorAll('tr[data-custom-row]')).find(function(tr) {
                const nameCell = tr.children[1];
                return nameCell && nameCell.textContent.trim() === name;
            }) || null;
        }
        if (!row) {
            row = document.createElement('tr');
            row.setAttribute('data-custom-row', 'true');
            row.innerHTML =
                '<td><button type="button" class="btn btn-link btn-sm food-favorite-btn food-favorite-btn--inline p-0"' +
                ' data-recipe-id="" data-favorite="false" onclick="toggleFoodFavorite(event, this)"' +
                ' title="Favorite this food"><i class="fas fa-star-o"></i></button></td>' +
                '<td class="font-weight-bold"></td>' +
                '<td><span class="badge badge-light"></span></td>' +
                '<td class="text-muted"></td>' +
                '<td class="font-weight-bold text-primary"></td>' +
                '<td><button type="button" class="btn btn-outline-primary btn-sm"' +
                ' data-food="" data-calories="" data-quantity="" data-unit="" data-source="Custom"' +
                ' data-grams="0" data-protein="0" data-fiber="0" data-name="" data-category=""' +
                ' onclick="addFoodFromButton(this); return false;">Add</button></td>';
            body.appendChild(row);
        }
        if (recipeId) row.setAttribute('data-recipe-id', String(recipeId));
        const star = row.querySelector('.food-favorite-btn');
        if (star && recipeId) {
            star.setAttribute('data-recipe-id', String(recipeId));
            star.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
            const icon = star.querySelector('i');
            if (icon) icon.className = isFavorite ? 'fas fa-star' : 'fas fa-star-o';
        }
        if (row.children[1]) row.children[1].textContent = name;
        const badge = row.children[2] && row.children[2].querySelector('.badge');
        if (badge) badge.textContent = category;
        if (row.children[3]) row.children[3].textContent = servingLabel;
        if (row.children[4]) row.children[4].textContent = calories + ' cal';
        const addBtn = row.querySelector('button.btn-outline-primary');
        if (addBtn) {
            addBtn.setAttribute('data-food', name);
            addBtn.setAttribute('data-name', name);
            addBtn.setAttribute('data-calories', String(calories));
            addBtn.setAttribute('data-quantity', String(quantity));
            addBtn.setAttribute('data-unit', unit);
            addBtn.setAttribute('data-category', category);
            addBtn.setAttribute('data-source', 'Custom');
            addBtn.setAttribute('data-protein', String(proteinG));
            addBtn.setAttribute('data-fiber', String(fiberG));
        }
    }

    const countEl = document.getElementById('customFoodsCount');
    if (countEl) {
        countEl.textContent = String(document.querySelectorAll('#customFoodsBody tr[data-custom-row]').length);
    }
    const customTab = document.getElementById('custom-tab');
    if (customTab) {
        const n = document.querySelectorAll('.food-item[data-custom="true"]').length;
        customTab.innerHTML = '<i class="fas fa-pen"></i> Custom (' + n + ')';
    }
    if (typeof updateFavoritesTabCount === 'function') {
        updateFavoritesTabCount();
    }
}

function saveCustomFoodToCatalog(
    name, calories, quantity, unit, foodCategory, proteinG, fiberG, notes
) {
    const cfg = window.LOG_FEEDING_CONFIG || {};
    const url = cfg.createRecipeUrl || '/api/recipes';
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin',
        body: JSON.stringify({
            meal_name: name,
            calories: calories,
            quantity: quantity,
            unit_of_measurement: unit,
            food_category: foodCategory || 'Other',
            source: 'Custom',
            description: notes || '',
            protein_g: proteinG || 0,
            fiber_g: fiberG || 0
        })
    })
        .then(function(response) {
            return response.json().then(function(data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function(result) {
            if (result.ok && result.data.success && result.data.recipe) {
                upsertCustomFoodInUi(result.data.recipe);
                return;
            }
            upsertCustomFoodInUi({
                id: result.data && result.data.recipe && result.data.recipe.id,
                meal_name: name,
                calories: calories,
                quantity: quantity,
                unit_of_measurement: unit,
                food_category: foodCategory,
                source: 'Custom',
                description: notes || '',
                protein_g: proteinG || 0,
                fiber_g: fiberG || 0,
                is_favorite: false
            });
        })
        .catch(function(error) {
            console.warn('Could not save custom food to catalog immediately:', error);
        });
}

function catalogServingLabelFromRecipe(recipe) {
    if (recipe.catalog_serving_label) {
        return recipe.catalog_serving_label;
    }
    const qty = recipe.quantity != null ? recipe.quantity : 1;
    const unit = recipe.unit_of_measurement || 'serving';
    if (qty === 1 || qty === 1.0) {
        return '1 ' + unit;
    }
    return qty + ' ' + unit;
}

function upsertCustomFoodInUi(recipe) {
    if (!recipe || !recipe.meal_name) {
        return;
    }
    const name = recipe.meal_name;
    const calories = recipe.calories;
    const quantity = recipe.quantity != null ? recipe.quantity : 1;
    const unit = recipe.unit_of_measurement || '';
    const category = recipe.food_category || 'Other';
    const recipeId = recipe.id;
    const isFavorite = !!recipe.is_favorite;
    const proteinG = recipe.protein_g || 0;
    const fiberG = recipe.fiber_g || 0;
    const servingLabel = catalogServingLabelFromRecipe(recipe);

    const grid = document.getElementById('foodsGrid');
    if (grid && recipeId) {
        let foodItem = grid.querySelector('.food-item[data-recipe-id="' + recipeId + '"]');
        if (!foodItem) {
            foodItem = Array.from(grid.querySelectorAll('.food-item')).find(function(el) {
                return (el.getAttribute('data-name') || '') === name.toLowerCase();
            }) || null;
        }
        if (!foodItem) {
            foodItem = document.createElement('div');
            foodItem.className = 'col-lg-3 col-md-4 col-sm-6 col-6 mb-2 food-item';
            foodItem.innerHTML =
                '<div class="food-card-wrap position-relative">' +
                '<button type="button" class="btn btn-link btn-sm food-favorite-btn p-0"' +
                ' data-recipe-id="" data-favorite="false" onclick="toggleFoodFavorite(event, this)"' +
                ' title="Favorite this food"><i class="fas fa-star-o"></i></button>' +
                '<span class="badge badge-secondary food-custom-badge">Custom</span>' +
                '<button type="button" class="btn btn-outline-primary w-100 h-100 py-2 quick-food-btn food-card"' +
                ' data-food="" data-calories="" data-quantity="" data-unit="" data-source="Custom"' +
                ' data-grams="0" data-protein="0" data-fiber="0" data-name="" data-category=""' +
                ' onclick="addFoodFromButton(this); return false;">' +
                '<div class="text-center">' +
                '<i class="fas fa-tag mb-1 text-secondary"></i>' +
                '<div class="d-block small font-weight-bold food-card-name"></div>' +
                '<small class="text-muted d-block food-card-serving"></small>' +
                '<small class="text-muted font-weight-bold food-card-cal"></small>' +
                '<small class="d-block text-secondary food-card-category"></small>' +
                '</div></button></div>';
            grid.appendChild(foodItem);
        }
        foodItem.setAttribute('data-recipe-id', recipeId || '');
        foodItem.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
        foodItem.setAttribute('data-custom', 'true');
        foodItem.setAttribute('data-category', category);
        foodItem.setAttribute('data-name', name.toLowerCase());
        foodItem.setAttribute('data-description', (recipe.description || '').toLowerCase());
        foodItem.setAttribute('data-calories', String(calories));

        const starBtn = foodItem.querySelector('.food-favorite-btn');
        if (starBtn) {
            starBtn.setAttribute('data-recipe-id', recipeId || '');
            starBtn.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
        }
        const cardBtn = foodItem.querySelector('.quick-food-btn');
        if (cardBtn) {
            cardBtn.setAttribute('data-food', name);
            cardBtn.setAttribute('data-name', name);
            cardBtn.setAttribute('data-calories', String(calories));
            cardBtn.setAttribute('data-quantity', String(quantity));
            cardBtn.setAttribute('data-unit', unit);
            cardBtn.setAttribute('data-source', 'Custom');
            cardBtn.setAttribute('data-category', category);
            cardBtn.setAttribute('data-protein', String(proteinG));
            cardBtn.setAttribute('data-fiber', String(fiberG));
        }
        const nameEl = foodItem.querySelector('.food-card-name');
        if (nameEl) nameEl.textContent = name;
        const servingEl = foodItem.querySelector('.food-card-serving');
        if (servingEl) servingEl.textContent = 'per ' + servingLabel;
        const calEl = foodItem.querySelector('.food-card-cal');
        if (calEl) calEl.textContent = calories + ' cal';
        const catEl = foodItem.querySelector('.food-card-category');
        if (catEl) catEl.textContent = category;
    }

    const body = document.getElementById('customFoodsBody');
    if (body) {
        const empty = document.getElementById('customFoodsEmptyRow');
        if (empty) empty.remove();
        let row = recipeId ? body.querySelector('tr[data-recipe-id="' + recipeId + '"]') : null;
        if (!row) {
            row = Array.from(body.querySelectorAll('tr[data-custom-row]')).find(function(tr) {
                const nameCell = tr.children[1];
                return nameCell && nameCell.textContent.trim() === name;
            }) || null;
        }
        if (!row) {
            row = document.createElement('tr');
            row.setAttribute('data-custom-row', 'true');
            row.innerHTML =
                '<td><button type="button" class="btn btn-link btn-sm food-favorite-btn food-favorite-btn--inline p-0"' +
                ' data-recipe-id="" data-favorite="false" onclick="toggleFoodFavorite(event, this)"' +
                ' title="Favorite this food"><i class="fas fa-star-o"></i></button></td>' +
                '<td class="font-weight-bold"></td>' +
                '<td><span class="badge badge-light"></span></td>' +
                '<td class="text-muted"></td>' +
                '<td class="font-weight-bold text-primary"></td>' +
                '<td><button type="button" class="btn btn-outline-primary btn-sm"' +
                ' data-food="" data-calories="" data-quantity="" data-unit="" data-source="Custom"' +
                ' data-grams="0" data-protein="0" data-fiber="0" data-name="" data-category=""' +
                ' onclick="addFoodFromButton(this); return false;">Add</button></td>';
            body.appendChild(row);
        }
        if (recipeId) row.setAttribute('data-recipe-id', String(recipeId));
        const star = row.querySelector('.food-favorite-btn');
        if (star && recipeId) {
            star.setAttribute('data-recipe-id', String(recipeId));
            star.setAttribute('data-favorite', isFavorite ? 'true' : 'false');
            const icon = star.querySelector('i');
            if (icon) icon.className = isFavorite ? 'fas fa-star' : 'fas fa-star-o';
        }
        if (row.children[1]) row.children[1].textContent = name;
        const badge = row.children[2] && row.children[2].querySelector('.badge');
        if (badge) badge.textContent = category;
        if (row.children[3]) row.children[3].textContent = servingLabel;
        if (row.children[4]) row.children[4].textContent = calories + ' cal';
        const addBtn = row.querySelector('button.btn-outline-primary');
        if (addBtn) {
            addBtn.setAttribute('data-food', name);
            addBtn.setAttribute('data-name', name);
            addBtn.setAttribute('data-calories', String(calories));
            addBtn.setAttribute('data-quantity', String(quantity));
            addBtn.setAttribute('data-unit', unit);
            addBtn.setAttribute('data-category', category);
            addBtn.setAttribute('data-source', 'Custom');
            addBtn.setAttribute('data-protein', String(proteinG));
            addBtn.setAttribute('data-fiber', String(fiberG));
        }
    }

    const countEl = document.getElementById('customFoodsCount');
    if (countEl) {
        countEl.textContent = String(document.querySelectorAll('#customFoodsBody tr[data-custom-row]').length);
    }
    const customTab = document.getElementById('custom-tab');
    if (customTab) {
        const n = document.querySelectorAll('.food-item[data-custom="true"]').length;
        customTab.innerHTML = '<i class="fas fa-pen"></i> Custom (' + n + ')';
    }
    if (typeof updateFavoritesTabCount === 'function') {
        updateFavoritesTabCount();
    }
}

