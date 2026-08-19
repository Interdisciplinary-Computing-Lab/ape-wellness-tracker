/** @file Save meals to server and success UI. */
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
    const dashboardUrl = (window.LOG_FEEDING_CONFIG && window.LOG_FEEDING_CONFIG.dashboardUrl) || '/dashboard';
    textEl.innerHTML =
        '<strong>Saved!</strong> Meals logged for <strong>' + apeLabel + '</strong> (' + mealLabel + ') — ' +
        '<span id="feedingSaveSuccessCal">' + cals + ' cal</span>. ' +
        'View them on the <a href="' + dashboardUrl + '" class="alert-link font-weight-bold">Dashboard</a> ' +
        'or each ape\'s profile.';
    el.classList.remove('d-none', 'is-hiding');
    el.classList.add('is-visible');
    feedingSaveSuccessTimer = setTimeout(function() {
        el.classList.add('is-hiding');
        feedingSaveSuccessTimer = setTimeout(function() {
            hideFeedingSaveSuccess();
            feedingSaveSuccessTimer = null;
        }, 500);
    }, 8000);
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
        const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;
        const loggedQty = item.quantity > 0 ? item.quantity : 1.0;
        return {
            name: item.name,
            calories: Math.round(item.calories || 0),
            quantity: loggedQty / catalogQty,
            recipe_quantity: catalogQty,
            unit: item.unit || '',
            source: item.source || '',
            food_category: item.foodCategory || '',
            protein_g: item.proteinPerCatalog || 0,
            fiber_g: item.fiberPerCatalog || 0,
            description: item.description || ''
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
    const mealType = (typeof getSelectedMealType === 'function')
        ? getSelectedMealType()
        : 'Forage';
    const feedingData = {
        ape_ids: Array.from(selectedApes),
        feeding_items: transformedItems,
        date: dateValue,
        feeding_period: periodEl ? periodEl.value : 'morning',
        meal_type: mealType
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
            clearFeedingList();
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
