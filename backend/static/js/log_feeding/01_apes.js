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
