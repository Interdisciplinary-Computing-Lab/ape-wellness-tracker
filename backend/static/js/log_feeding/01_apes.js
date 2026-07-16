/** @file Ape selection for log feeding. */
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

function sessionTotalCalories() {
    let totalCal = 0;
    feedingItems.forEach(function(itm) {
        if (!itm.caloriesInvalid && itm.totalCalories != null) {
            totalCal += itm.totalCalories;
        }
    });
    return totalCal;
}

function getSavedApeCalories(apeId) {
    var cfg = window.LOG_FEEDING_CONFIG || {};
    var map = cfg.apeCaloriesToday || {};
    return Math.round(map[apeId] || map[String(apeId)] || 0);
}

function getSavedMealBreakdown(apeId) {
    var cfg = window.LOG_FEEDING_CONFIG || {};
    var map = cfg.apeMealCaloriesToday || {};
    var raw = map[apeId] || map[String(apeId)] || {};
    return {
        Breakfast: Math.round(raw.Breakfast || 0),
        Lunch: Math.round(raw.Lunch || 0),
        Dinner: Math.round(raw.Dinner || 0)
    };
}

function isLoggingForToday() {
    var cfg = window.LOG_FEEDING_CONFIG || {};
    var dateEl = document.getElementById('feedingDate');
    var selected = dateEl && dateEl.value ? dateEl.value : (cfg.defaultFeedingDate || '');
    return selected && selected === cfg.defaultFeedingDate;
}

function formatCalorieLabel(value) {
    return Math.round(value) + ' <span class="text-muted font-weight-normal">cal</span>';
}

function updateStats() {
    var sessionCal = sessionTotalCalories();
    var hasFoods = feedingItems.length > 0;
    var includeSession = hasFoods && isLoggingForToday();
    var mealType = (typeof getSelectedMealType === 'function')
        ? getSelectedMealType()
        : 'Breakfast';
    if (mealType !== 'Breakfast' && mealType !== 'Lunch' && mealType !== 'Dinner') {
        mealType = 'Breakfast';
    }
    var labels = (window.LOG_FEEDING_CONFIG && window.LOG_FEEDING_CONFIG.mealTypeLabels)
        || ['Breakfast', 'Lunch', 'Dinner'];

    document.querySelectorAll('[data-ape-calories-block]').forEach(function(block) {
        var apeId = parseInt(block.getAttribute('data-ape-calories-block'), 10);
        var isSelected = selectedApes.has(apeId);
        var savedTotal = getSavedApeCalories(apeId);
        var breakdown = getSavedMealBreakdown(apeId);
        var displayTotal = savedTotal;
        var displayBreakdown = {
            Breakfast: breakdown.Breakfast,
            Lunch: breakdown.Lunch,
            Dinner: breakdown.Dinner
        };

        if (includeSession && isSelected) {
            displayTotal += sessionCal;
            displayBreakdown[mealType] += sessionCal;
        }

        var totalEl = block.querySelector('[data-ape-calories]');
        if (totalEl) {
            totalEl.innerHTML = formatCalorieLabel(displayTotal);
            if (includeSession && isSelected && sessionCal > 0) {
                totalEl.classList.add('text-success');
                totalEl.classList.remove('text-muted');
            } else {
                totalEl.classList.remove('text-success');
            }
        }

        labels.forEach(function(label) {
            var cell = block.querySelector('[data-meal-type="' + label + '"]');
            if (cell) {
                cell.innerHTML = formatCalorieLabel(displayBreakdown[label] || 0);
                if (includeSession && isSelected && sessionCal > 0 && label === mealType) {
                    cell.classList.add('text-success');
                } else {
                    cell.classList.remove('text-success');
                }
            }
        });
    });

    var perApeEl = document.getElementById('perApeCalories');
    if (perApeEl) {
        if (selectedApes.size > 0 && hasFoods) {
            perApeEl.textContent = Math.round(sessionCal);
        } else {
            perApeEl.textContent = '—';
        }
    }
}

function updateSaveButton() {
    const saveBtn = document.getElementById('saveFeedingBtn');
    if (!saveBtn) {
        return;
    }
    saveBtn.disabled = selectedApes.size === 0 || feedingItems.length === 0;
}
