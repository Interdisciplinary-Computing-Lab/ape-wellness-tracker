/**
 * Edit saved meal entries from dashboard / ape profile activity tables.
 */
(function(global) {
    'use strict';

    const FN = global.FeedingNutrition;
    let editItem = null;
    let saveInProgress = false;

    function recipesIndex() {
        const list = global.MEAL_EDIT_RECIPES || [];
        const byId = {};
        const byName = {};
        list.forEach(function(r) {
            byId[r.id] = r;
            byName[r.meal_name.toLowerCase()] = r;
        });
        return { byId: byId, byName: byName, list: list };
    }

    function findRecipeByName(name) {
        const key = (name || '').trim().toLowerCase();
        if (!key) return null;
        return recipesIndex().byName[key] || null;
    }

    function recipeToItem(recipe, quantity, unit) {
        if (!FN || !recipe) return null;
        return FN.buildFeedingItem({
            name: recipe.meal_name,
            calories: recipe.calories,
            recipeQuantity: recipe.quantity,
            unitRaw: recipe.unit_of_measurement || unit || '',
            source: recipe.source || '',
            gramsPerServing: recipe.gram_weight || 0,
            proteinG: recipe.protein_g,
            fiberG: recipe.fiber_g,
        });
    }

    function populateUnitSelect(item) {
        const select = document.getElementById('mealEditUnit');
        if (!select || !FN) return;
        const units = FN.unitsForItem(item);
        const current = item.unit || 'serving';
        select.innerHTML = '';
        units.forEach(function(u) {
            const opt = document.createElement('option');
            opt.value = u;
            opt.textContent = u;
            if (u === current) opt.selected = true;
            select.appendChild(opt);
        });
    }

    function refreshCaloriesDisplay() {
        const calInput = document.getElementById('mealEditCalories');
        const hint = document.getElementById('mealEditCaloriesHint');
        if (!editItem || !calInput) return;

        FN.recalculateItem(editItem);
        if (editItem.caloriesInvalid) {
            calInput.value = '';
            calInput.disabled = true;
            calInput.classList.add('text-danger');
            if (hint) {
                hint.textContent = 'This unit does not match how this food is stored. Pick another unit or food.';
                hint.classList.add('text-danger');
            }
            return;
        }
        calInput.disabled = false;
        calInput.classList.remove('text-danger');
        if (hint) hint.classList.remove('text-danger');
        const total = editItem.totalCalories != null ? editItem.totalCalories : 0;
        if (document.activeElement !== calInput) {
            calInput.value = Math.round(total);
        }
        if (hint) {
            hint.textContent = editItem.name + ' · catalog base ' + (editItem.calories || 0) + ' cal · qty auto-adjusts when you edit calories';
        }
    }

    function applyCaloriesToItem(targetCalories) {
        if (!editItem || isNaN(targetCalories) || targetCalories < 0) return;

        editItem.caloriesOverride = targetCalories;
        editItem.manualCalories = true;
        if (editItem.calories > 0) {
            let newQty = FN.quantityForTargetCalories(editItem, targetCalories);
            if (isNaN(newQty) || newQty <= 0) {
                const catalogQty = editItem.recipeQuantity > 0 ? editItem.recipeQuantity : 1.0;
                newQty = (targetCalories / editItem.calories) * catalogQty;
            }
            if (!isNaN(newQty) && newQty > 0) {
                editItem.quantity = Math.round(newQty * 1000) / 1000;
                const qtyInput = document.getElementById('mealEditQuantity');
                if (qtyInput && document.activeElement !== qtyInput) {
                    qtyInput.value = FN.formatQuantity(editItem.quantity);
                }
            }
        }
        refreshCaloriesDisplay();
    }

    function loadItemFromRecipe(recipe, quantity, unit) {
        editItem = recipeToItem(recipe, quantity, unit);
        if (!editItem) return;
        if (quantity != null) editItem.quantity = parseFloat(quantity) || 1;
        if (unit) editItem.unit = FN.normalizeUnit(unit);
        document.getElementById('mealEditRecipeId').value = recipe.id;
        document.getElementById('mealEditFoodSearch').value = recipe.meal_name;
        document.getElementById('mealEditQuantity').value = FN.formatQuantity(editItem.quantity);
        populateUnitSelect(editItem);
        refreshCaloriesDisplay();
    }

    function loadItemFromApi(meal) {
        const idx = recipesIndex();
        let recipe = idx.byId[meal.recipe_id];
        if (!recipe && meal.food_name) {
            recipe = findRecipeByName(meal.food_name);
        }
        if (recipe) {
            const qty = meal.quantity != null ? meal.quantity : 1;
            loadItemFromRecipe(recipe, qty, meal.unit_raw || meal.unit);
            if (meal.calories_logged > 0 && editItem) {
                const target = meal.calories_logged;
                if (Math.abs((editItem.totalCalories || 0) - target) > 1) {
                    applyCaloriesToItem(target);
                }
            }
            document.getElementById('mealEditQuantity').value = FN.formatQuantity(editItem.quantity);
            populateUnitSelect(editItem);
            refreshCaloriesDisplay();
        } else {
            editItem = {
                name: meal.food_name,
                calories: meal.catalog_calories || meal.calories_logged,
                recipeQuantity: meal.recipe_quantity || 1,
                quantity: meal.quantity || 1,
                unit: meal.unit || 'serving',
                source: meal.source || '',
                gramsPerServing: meal.gram_weight || 0,
                proteinPerCatalog: meal.protein_g || 0,
                fiberPerCatalog: meal.fiber_g || 0,
                catalogUnit: 'serving',
                caloriesInvalid: false,
                manualCalories: false,
                caloriesOverride: null,
            };
            document.getElementById('mealEditRecipeId').value = meal.recipe_id || '';
            document.getElementById('mealEditFoodSearch').value = meal.food_name;
            document.getElementById('mealEditQuantity').value = meal.quantity;
            const select = document.getElementById('mealEditUnit');
            if (select) {
                select.innerHTML = '<option value="' + meal.unit + '">' + meal.unit + '</option>';
            }
            refreshCaloriesDisplay();
        }
        document.getElementById('mealEditApe').value = String(meal.ape_id);
        document.getElementById('mealEditDate').value = meal.date;
        var period = meal.feeding_period || 'morning';
        if (period === 'night') {
            period = 'evening';
        }
        document.getElementById('mealEditPeriod').value = period;
        var mealTypeEl = document.getElementById('mealEditMealType');
        if (mealTypeEl) {
            var mt = meal.meal_type || MEAL_TYPE_BY_PERIOD[period] || 'Forage';
            mealTypeEl.value = mt;
        }
        document.getElementById('mealEditId').value = meal.id;
    }

    function showError(msg) {
        const el = document.getElementById('mealEditError');
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('d-none');
    }

    function hideError() {
        const el = document.getElementById('mealEditError');
        if (el) el.classList.add('d-none');
    }

    function showFlash(msg) {
        const el = document.getElementById('mealEditFlash');
        if (!el) return;
        el.textContent = msg;
        el.classList.remove('d-none');
        el.classList.add('show');
        setTimeout(function() {
            el.classList.add('d-none');
            el.classList.remove('show');
        }, 4000);
    }

    function openMealEditor(mealId) {
        if (!mealId || !global.jQuery) return;
        hideError();
        editItem = null;
        const modal = global.jQuery('#mealEditModal');
        modal.modal('show');
        document.getElementById('mealEditSaveBtn').disabled = true;

        fetch('/api/meals/' + encodeURIComponent(mealId), {
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then(function(res) {
                return res.json().then(function(data) {
                    return { ok: res.ok, data: data };
                });
            })
            .then(function(result) {
                if (!result.ok || !result.data.success) {
                    showError(result.data.error || 'Could not load meal');
                    return;
                }
                loadItemFromApi(result.data.meal);
                document.getElementById('mealEditSaveBtn').disabled = false;
            })
            .catch(function() {
                showError('Could not load meal');
            });
    }

    function onFoodChange() {
        const name = document.getElementById('mealEditFoodSearch').value.trim();
        const recipe = findRecipeByName(name);
        if (!recipe) {
            showError('Pick a food from the list');
            return;
        }
        hideError();
        const qty = parseFloat(document.getElementById('mealEditQuantity').value) || 1;
        const unit = document.getElementById('mealEditUnit').value;
        loadItemFromRecipe(recipe, qty, unit);
    }

    function onQtyOrUnitChange() {
        if (!editItem) return;
        editItem.manualCalories = false;
        editItem.caloriesOverride = null;
        editItem.quantity = parseFloat(document.getElementById('mealEditQuantity').value) || 1;
        editItem.unit = FN.normalizeUnit(document.getElementById('mealEditUnit').value);
        refreshCaloriesDisplay();
    }

    function onCaloriesChange() {
        if (!editItem) return;
        const v = parseInt(document.getElementById('mealEditCalories').value, 10);
        if (isNaN(v) || v < 0) return;
        applyCaloriesToItem(v);
    }

    function buildPayload() {
        if (!editItem) return null;
        FN.recalculateItem(editItem);
        if (editItem.caloriesInvalid) return null;
        return {
            ape_id: parseInt(document.getElementById('mealEditApe').value, 10),
            recipe_id: parseInt(document.getElementById('mealEditRecipeId').value, 10) || null,
            food_name: editItem.name,
            date: document.getElementById('mealEditDate').value,
            feeding_period: document.getElementById('mealEditPeriod').value,
            meal_type: (document.getElementById('mealEditMealType') || {}).value || 'Forage',
            calories: Math.round(editItem.totalCalories || 0),
            quantity: 1.0,
            unit: editItem.unit || '',
            source: editItem.source || '',
        };
    }

    function saveMealEdit() {
        if (saveInProgress) return;
        const mealId = document.getElementById('mealEditId').value;
        const payload = buildPayload();
        if (!payload) {
            showError('Fix calories / unit before saving');
            return;
        }
        if (payload.calories <= 0) {
            showError('Calories must be greater than zero');
            return;
        }

        saveInProgress = true;
        const btn = document.getElementById('mealEditSaveBtn');
        const original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i>Saving…';

        fetch('/api/meals/' + encodeURIComponent(mealId), {
            method: 'PATCH',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(payload),
        })
            .then(function(res) {
                return res.json().then(function(data) {
                    return { ok: res.ok, data: data };
                });
            })
            .then(function(result) {
                if (result.ok && result.data.success) {
                    global.jQuery('#mealEditModal').modal('hide');
                    showFlash('Meal updated — ' + payload.calories.toLocaleString() + ' cal');
                    setTimeout(function() {
                        global.location.reload();
                    }, 600);
                } else {
                    showError(result.data.error || 'Save failed');
                }
            })
            .catch(function() {
                showError('Save failed');
            })
            .finally(function() {
                saveInProgress = false;
                btn.disabled = false;
                btn.innerHTML = original;
            });
    }

    function deleteMealEdit() {
        const mealId = document.getElementById('mealEditId').value;
        if (!mealId || !global.confirm('Remove this meal entry? This cannot be undone.')) {
            return;
        }
        fetch('/api/meals/' + encodeURIComponent(mealId), {
            method: 'DELETE',
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
            .then(function(res) {
                return res.json().then(function(data) {
                    return { ok: res.ok, data: data };
                });
            })
            .then(function(result) {
                if (result.ok && result.data.success) {
                    global.jQuery('#mealEditModal').modal('hide');
                    showFlash('Meal entry removed');
                    setTimeout(function() {
                        global.location.reload();
                    }, 600);
                } else {
                    showError(result.data.error || 'Delete failed');
                }
            })
            .catch(function() {
                showError('Delete failed');
            });
    }

    var MEAL_TYPE_BY_PERIOD = {
        morning: 'Forage',
        afternoon: 'Enrichment',
        evening: 'Reward'
    };

    function updateMealEditMealTypeLabel() {
        var periodEl = document.getElementById('mealEditPeriod');
        var mealTypeEl = document.getElementById('mealEditMealType');
        if (!periodEl || !mealTypeEl) return;
        var period = periodEl.value || 'morning';
        if (period === 'night') {
            period = 'evening';
            periodEl.value = 'evening';
        }
        mealTypeEl.value = MEAL_TYPE_BY_PERIOD[period] || 'Forage';
    }

    function bindControls() {
        const foodInput = document.getElementById('mealEditFoodSearch');
        const qtyInput = document.getElementById('mealEditQuantity');
        const unitSelect = document.getElementById('mealEditUnit');
        const calInput = document.getElementById('mealEditCalories');
        const saveBtn = document.getElementById('mealEditSaveBtn');
        const deleteBtn = document.getElementById('mealEditDeleteBtn');
        const periodEl = document.getElementById('mealEditPeriod');

        if (foodInput) {
            foodInput.addEventListener('change', onFoodChange);
            foodInput.addEventListener('blur', onFoodChange);
        }
        if (qtyInput) qtyInput.addEventListener('input', onQtyOrUnitChange);
        if (unitSelect) unitSelect.addEventListener('change', onQtyOrUnitChange);
        if (calInput) calInput.addEventListener('input', onCaloriesChange);
        if (saveBtn) saveBtn.addEventListener('click', saveMealEdit);
        if (deleteBtn) deleteBtn.addEventListener('click', deleteMealEdit);
        if (periodEl) periodEl.addEventListener('change', updateMealEditMealTypeLabel);

        document.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-meal-edit]');
            if (!btn) return;
            e.preventDefault();
            const mealId = btn.getAttribute('data-meal-edit');
            openMealEditor(mealId);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindControls);
    } else {
        bindControls();
    }

    global.openMealEditor = openMealEditor;
    global.updateMealEditMealTypeLabel = updateMealEditMealTypeLabel;
})(window);
