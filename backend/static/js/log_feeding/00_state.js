/** @file Log feeding shared state and nutrition helpers. */
let selectedApes = new Set();
let feedingItems = [];
let saveFeedingInProgress = false;
let feedingSaveSuccessTimer = null;
let currentCategory = 'all'; // Shared catalog; init opens the full list (see 05_init.js)
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
