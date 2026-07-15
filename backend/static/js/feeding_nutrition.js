/**
 * Portion nutrition math for log feeding (USDA FDC gram-weight scaling).
 */
(function (global) {
    'use strict';

    const VOLUME_TO_CUP = { cup: 1, tbsp: 0.0625, tsp: 0.0208333 };
    const WEIGHT_TO_G = { g: 1, oz: 28.3495, lb: 453.592 };
    const COUNT_UNITS = ['piece', 'whole', 'slice', 'serving'];
    const WEIGHT_UNITS = ['g', 'oz', 'lb'];
    const VOLUME_UNITS = ['cup', 'tbsp', 'tsp'];

    const STANDARD_UNIT_ALIASES = {
        cup: ['cup', 'cups'],
        tbsp: ['tbsp', 'tablespoon', 'tablespoons', 'tbs'],
        tsp: ['tsp', 'teaspoon', 'teaspoons'],
        g: ['g', 'gram', 'grams', 'gm'],
        oz: ['oz', 'ounce', 'ounces'],
        lb: ['lb', 'lbs', 'pound', 'pounds'],
        piece: ['piece', 'pieces', 'pc', 'whole', 'wholes'],
        slice: ['slice', 'slices'],
        serving: ['serving', 'servings'],
    };

    function formatQuantity(qty) {
        if (qty === null || qty === undefined || isNaN(qty)) return '1';
        const rounded = Math.round(qty * 100) / 100;
        if (rounded === Math.floor(rounded)) return String(Math.floor(rounded));
        return rounded.toFixed(2).replace(/\.?0+$/, '');
    }

    function matchStandardUnit(token) {
        if (!token) return null;
        const t = token.toLowerCase().trim();
        for (const [canonical, aliases] of Object.entries(STANDARD_UNIT_ALIASES)) {
            if (aliases.includes(t)) return canonical;
        }
        if (/\bcups?\b/.test(t)) return 'cup';
        if (/\btbsp\b|\btablespoon/.test(t)) return 'tbsp';
        if (/\btsp\b|\bteaspoon/.test(t)) return 'tsp';
        return null;
    }

    /** Parse recipe.unit_of_measurement with recipe.quantity from DB. */
    function parseCatalogUnit(unitStr, recipeQuantity) {
        const raw = (unitStr || '').trim();
        let catalogQuantity = recipeQuantity > 0 ? recipeQuantity : 1.0;
        let unitPart = raw;
        let catalogVolumeCups = null;

        if (/^100\s*g$/i.test(raw)) {
            return {
                catalogQuantity: 100,
                catalogUnit: 'g',
                servingLabel: '100 g',
                foodSpecificServing: false,
                per100g: true,
                catalogVolumeCups: null,
            };
        }

        const leading = raw.match(/^(\d+(?:\.\d+)?)\s+(.+)$/);
        if (leading) {
            const n = parseFloat(leading[1]);
            if (!isNaN(n) && n > 0) {
                catalogQuantity = n;
                unitPart = leading[2].trim();
            }
        }

        const std = matchStandardUnit(unitPart);
        if (std === 'g' && catalogQuantity === 100) {
            return {
                catalogQuantity: 100,
                catalogUnit: 'g',
                servingLabel: raw || '100 g',
                foodSpecificServing: false,
                per100g: true,
                catalogVolumeCups: null,
            };
        }

        if (std) {
            if (VOLUME_UNITS.includes(std)) {
                catalogVolumeCups = catalogQuantity;
            }
            return {
                catalogQuantity,
                catalogUnit: std,
                servingLabel: raw || std,
                foodSpecificServing: false,
                per100g: false,
                catalogVolumeCups,
            };
        }

        if (/\bcups?\b/i.test(unitPart)) {
            catalogVolumeCups = catalogQuantity;
        }

        return {
            catalogQuantity,
            catalogUnit: 'serving',
            servingLabel: unitPart || 'serving',
            foodSpecificServing: true,
            per100g: false,
            catalogVolumeCups,
        };
    }

    function normalizeUnit(unit) {
        if (!unit || !String(unit).trim()) return 'serving';
        const parsed = parseCatalogUnit(String(unit).trim(), 1);
        if (!parsed.foodSpecificServing) return parsed.catalogUnit;
        if (parsed.catalogVolumeCups != null) return 'cup';
        return 'serving';
    }

    function getUnitCategory(unit) {
        const u = normalizeUnit(unit);
        if (Object.prototype.hasOwnProperty.call(VOLUME_TO_CUP, u)) return 'volume';
        if (Object.prototype.hasOwnProperty.call(WEIGHT_TO_G, u)) return 'weight';
        if (COUNT_UNITS.includes(u)) return 'count';
        return 'other';
    }

    function canConvertUnits(fromUnit, toUnit) {
        const a = getUnitCategory(fromUnit);
        const b = getUnitCategory(toUnit);
        return a !== 'other' && a === b;
    }

    function convertUnit(quantity, fromUnit, toUnit) {
        if (fromUnit === toUnit) return quantity;
        if (!fromUnit || !toUnit) return quantity;

        const fromCat = getUnitCategory(fromUnit);
        const toCat = getUnitCategory(toUnit);
        if (fromCat !== toCat || fromCat === 'other') return NaN;

        if (fromCat === 'volume') {
            const cups = quantity * (VOLUME_TO_CUP[fromUnit] || 1);
            return cups / (VOLUME_TO_CUP[toUnit] || 1);
        }
        if (fromCat === 'weight') {
            const grams = quantity * (WEIGHT_TO_G[fromUnit] || 1);
            return grams / (WEIGHT_TO_G[toUnit] || 1);
        }
        if (fromCat === 'count') return quantity;
        return NaN;
    }

    /** FDC reference weight in grams for one catalog serving (e.g. 100 for per 100 g). */
    function referenceGrams(item) {
        if (item.gramsPerServing > 0) return item.gramsPerServing;
        if (item.per100g || (item.catalogUnit === 'g' && item.recipeQuantity > 0)) {
            return item.recipeQuantity > 0 ? item.recipeQuantity : 100;
        }
        return 0;
    }

    /** Grams consumed from logged qty + unit using USDA portion weight. */
    function loggedGrams(item) {
        const qty = item.quantity > 0 ? item.quantity : 1.0;
        const displayUnit = normalizeUnit(item.unit || item.catalogUnit);
        const refG = referenceGrams(item);
        const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;

        if (refG <= 0) return NaN;

        const cat = getUnitCategory(displayUnit);

        if (COUNT_UNITS.includes(displayUnit)) {
            return (qty / catalogQty) * refG;
        }

        if (cat === 'weight') {
            return convertUnit(qty, displayUnit, 'g');
        }

        if (cat === 'volume') {
            const catalogCups = item.catalogVolumeCups;
            if (catalogCups != null && catalogCups > 0) {
                const cups = convertUnit(qty, displayUnit, 'cup');
                if (isNaN(cups)) return NaN;
                return (cups / catalogCups) * refG;
            }
            return NaN;
        }

        if (displayUnit === item.catalogUnit && !item.foodSpecificServing) {
            if (item.catalogUnit === 'g') {
                return qty;
            }
            return (qty / catalogQty) * refG;
        }

        return NaN;
    }

    function amountInCatalogUnits(item) {
        item.approximateCalories = false;
        const refG = referenceGrams(item);
        const grams = loggedGrams(item);
        if (isNaN(grams) || grams < 0 || refG <= 0) return NaN;

        const displayUnit = normalizeUnit(item.unit);
        if (item.per100g && getUnitCategory(displayUnit) === 'volume') {
            return NaN;
        }
        if (item.per100g && COUNT_UNITS.includes(displayUnit)) {
            return NaN;
        }

        if (displayUnit !== item.catalogUnit && !item.per100g && !COUNT_UNITS.includes(displayUnit)) {
            item.approximateCalories = getUnitCategory(displayUnit) !== getUnitCategory(item.catalogUnit);
        }

        return (grams / refG) * (item.recipeQuantity > 0 ? item.recipeQuantity : 1.0);
    }

    /** Default qty + unit for one full catalog serving when a food is added. */
    function defaultLoggedServing(parsed) {
        if (parsed.per100g) {
            return { quantity: parsed.catalogQuantity, unit: 'g' };
        }
        if (parsed.catalogVolumeCups != null) {
            return { quantity: parsed.catalogQuantity, unit: 'cup' };
        }
        if (parsed.foodSpecificServing) {
            return { quantity: 1.0, unit: 'serving' };
        }
        if (
            VOLUME_UNITS.includes(parsed.catalogUnit) ||
            WEIGHT_UNITS.includes(parsed.catalogUnit) ||
            COUNT_UNITS.includes(parsed.catalogUnit)
        ) {
            return { quantity: parsed.catalogQuantity, unit: parsed.catalogUnit };
        }
        return {
            quantity: parsed.catalogQuantity > 0 ? parsed.catalogQuantity : 1.0,
            unit: parsed.catalogUnit || 'serving',
        };
    }

    /** Amount to add when the same food is clicked again (one more catalog serving). */
    function catalogServingIncrement(item) {
        if (!item) return 1;
        const catQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1;
        const displayUnit = normalizeUnit(item.unit);

        if (item.per100g && displayUnit === 'g') {
            return catQty;
        }
        if (item.catalogVolumeCups != null && displayUnit === 'cup') {
            return catQty;
        }
        if (displayUnit === item.catalogUnit && !item.foodSpecificServing) {
            return catQty;
        }
        if (item.foodSpecificServing && displayUnit === 'serving') {
            return 1;
        }

        const refG = referenceGrams(item);
        if (refG > 0 && getUnitCategory(displayUnit) === 'weight') {
            const delta = convertUnit(refG, 'g', displayUnit);
            if (!isNaN(delta) && delta > 0) {
                return delta;
            }
        }
        if (item.catalogVolumeCups != null && getUnitCategory(displayUnit) === 'volume') {
            const delta = convertUnit(item.catalogVolumeCups, 'cup', displayUnit);
            if (!isNaN(delta) && delta > 0) {
                return delta;
            }
        }
        return 1;
    }

    function unitsForItem(item) {
        if (item.per100g || (item.catalogUnit === 'g' && item.recipeQuantity >= 100)) {
            return WEIGHT_UNITS.slice();
        }
        if (item.catalogVolumeCups != null) {
            return ['serving', 'cup', 'tbsp', 'tsp', 'g', 'oz', 'lb'];
        }
        if (item.foodSpecificServing) {
            return ['serving', 'piece', 'whole', 'slice', 'g', 'oz', 'lb'];
        }
        if (item.catalogUnit === 'g') {
            return WEIGHT_UNITS.slice();
        }
        if (VOLUME_UNITS.includes(item.catalogUnit)) {
            return VOLUME_UNITS.concat(WEIGHT_UNITS);
        }
        return ['piece', 'whole', 'serving', 'cup', 'g', 'oz', 'tbsp', 'tsp', 'slice', 'lb'];
    }

    function buildFeedingItem(opts) {
        const parsed = parseCatalogUnit(opts.unitRaw || '', opts.recipeQuantity || 1);
        const recipeQuantity = parsed.catalogQuantity;
        const catalogCalories = opts.calories > 0 ? opts.calories : 0;
        let gramsPerServing = opts.gramsPerServing > 0 ? opts.gramsPerServing : 0;
        if (!gramsPerServing && parsed.per100g) {
            gramsPerServing = 100;
        }

        const serving = defaultLoggedServing(parsed);
        const defaultUnit = serving.unit;
        const defaultQuantity = serving.quantity;

        const item = {
            name: opts.name,
            calories: catalogCalories,
            recipeQuantity,
            catalogUnit: parsed.catalogUnit,
            servingLabel: parsed.servingLabel,
            foodSpecificServing: parsed.foodSpecificServing,
            per100g: parsed.per100g,
            catalogVolumeCups: parsed.catalogVolumeCups,
            originalRecipeUnit: defaultUnit,
            proteinPerCatalog: opts.proteinG != null ? opts.proteinG : 0,
            fiberPerCatalog: opts.fiberG != null ? opts.fiberG : 0,
            quantity: defaultQuantity,
            unit: defaultUnit,
            source: opts.source || '',
            caloriesOverride: null,
            manualCalories: false,
            gramsPerServing,
            caloriesInvalid: false,
            crossUnitNote: false,
            totalCalories: null,
            totalProtein: null,
            totalFiber: null,
        };
        recalculateItem(item);
        return item;
    }

    /** Quantity in the item's current unit so logged calories match targetCalories. */
    function quantityForTargetCalories(item, targetCalories) {
        if (!item || targetCalories < 0 || item.calories <= 0) return NaN;

        const refG = referenceGrams(item);
        if (refG <= 0) return NaN;

        const desiredScale = targetCalories / item.calories;
        const desiredGrams = desiredScale * refG;
        const displayUnit = normalizeUnit(item.unit || item.catalogUnit);
        const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;

        if (COUNT_UNITS.includes(displayUnit)) {
            return desiredScale * catalogQty;
        }

        const cat = getUnitCategory(displayUnit);
        if (cat === 'weight') {
            return convertUnit(desiredGrams, 'g', displayUnit);
        }

        if (cat === 'volume') {
            const catalogCups = item.catalogVolumeCups;
            if (catalogCups != null && catalogCups > 0) {
                const cups = (desiredGrams / refG) * catalogCups;
                return convertUnit(cups, 'cup', displayUnit);
            }
            return NaN;
        }

        if (displayUnit === item.catalogUnit && !item.foodSpecificServing) {
            if (item.catalogUnit === 'g') {
                return desiredGrams;
            }
            return desiredScale * catalogQty;
        }

        return NaN;
    }

    function recalculateItem(item) {
        if (!item) return 0;

        if (item.manualCalories && item.caloriesOverride != null) {
            item.totalCalories = Math.max(0, Math.round(item.caloriesOverride));
            item.caloriesInvalid = false;
            const scale =
                item.calories > 0 && item.recipeQuantity > 0
                    ? item.totalCalories / item.calories
                    : 1;
            item.totalProtein = round1((item.proteinPerCatalog || 0) * scale);
            item.totalFiber = round1((item.fiberPerCatalog || 0) * scale);
            return item.totalCalories;
        }

        const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;
        const cal = item.calories;
        if (cal == null || isNaN(cal) || cal < 0) {
            item.caloriesInvalid = true;
            item.totalCalories = null;
            item.totalProtein = null;
            item.totalFiber = null;
            return 0;
        }

        const refG = referenceGrams(item);
        const grams = loggedGrams(item);

        if (refG > 0 && !isNaN(grams) && grams >= 0) {
            const scale = grams / refG;
            item.caloriesInvalid = false;
            item.totalCalories = Math.max(0, Math.round(cal * scale));
            item.totalProtein = round1((item.proteinPerCatalog || 0) * scale);
            item.totalFiber = round1((item.fiberPerCatalog || 0) * scale);
            return item.totalCalories;
        }

        const loggedQty = item.quantity > 0 ? item.quantity : 1.0;
        const scale = loggedQty / catalogQty;
        item.caloriesInvalid = false;
        item.totalCalories = Math.max(0, Math.round(cal * scale));
        item.totalProtein = round1((item.proteinPerCatalog || 0) * scale);
        item.totalFiber = round1((item.fiberPerCatalog || 0) * scale);
        return item.totalCalories;
    }

    function round1(n) {
        return Math.round(n * 10) / 10;
    }

    global.FeedingNutrition = {
        ALL_FEEDING_UNITS: ['piece', 'whole', 'serving', 'cup', 'g', 'oz', 'tbsp', 'tsp', 'slice', 'lb'],
        WEIGHT_UNITS,
        VOLUME_UNITS,
        formatQuantity,
        parseCatalogUnit,
        normalizeUnit,
        getUnitCategory,
        canConvertUnits,
        convertUnit,
        referenceGrams,
        loggedGrams,
        amountInCatalogUnits,
        unitsForItem,
        defaultLoggedServing,
        catalogServingIncrement,
        buildFeedingItem,
        quantityForTargetCalories,
        recalculateItem,
    };
})(typeof window !== 'undefined' ? window : global);
