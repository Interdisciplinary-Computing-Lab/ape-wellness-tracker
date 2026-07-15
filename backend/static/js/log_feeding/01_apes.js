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

function updateStats() {
    const totalCal = sessionTotalCalories();
    const hasFoods = feedingItems.length > 0;
    const showCalories = hasFoods;

    document.querySelectorAll('[data-ape-calories]').forEach(function(el) {
        const apeId = parseInt(el.getAttribute('data-ape-calories'), 10);
        const isSelected = selectedApes.has(apeId);
        if (isSelected && showCalories) {
            el.textContent = Math.round(totalCal) + ' cal';
            el.classList.remove('text-muted');
            el.classList.add('text-success', 'font-weight-bold');
        } else {
            el.textContent = '—';
            el.classList.remove('text-success', 'font-weight-bold');
            el.classList.add('text-muted');
        }
    });

    const perApeEl = document.getElementById('perApeCalories');
    if (perApeEl) {
        if (selectedApes.size > 0 && showCalories) {
            perApeEl.textContent = Math.round(totalCal);
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
