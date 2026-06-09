/** @file DOM ready, keyboard shortcuts, dates, global exports. */
document.addEventListener('DOMContentLoaded', function() {
    updateSelectedCount();
    updateStats();
    updateSaveButton();
    
    // Shared facility catalog: every account sees the same foods — show all by default
    filterByCategory('all', document.getElementById('all-tab'));

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
