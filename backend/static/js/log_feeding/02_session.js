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

    const item = feedingItems[index];
    item.quantity = newQuantity;
    if (!item.manualCalories) {
        item.caloriesOverride = null;
    }
    syncRowFromItem(index, flash);
}

function applyCaloriesChange(index, targetCalories) {
    if (index < 0 || index >= feedingItems.length) return;
    if (isNaN(targetCalories) || targetCalories < 0) return;

    const item = feedingItems[index];
    if (!item.manualCalories) return;

    item.caloriesOverride = targetCalories;
    if (item.calories > 0) {
        const newQty = FN.quantityForTargetCalories(item, targetCalories);
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
