/**
 * Portion nutrition math for log feeding (catalog Recipe vs logged qty/unit).
 */
(function (global) {
    'use strict';

    const VOLUME_TO_CUP = { cup: 1, tbsp: 0.0625, tsp: 0.0208333 };
    const WEIGHT_TO_G = { g: 1, oz: 28.3495, lb: 453.592 };
    const COUNT_UNITS = ['piece', 'slice', 'serving'];

    const STANDARD_UNIT_ALIASES = {
        cup: ['cup', 'cups'],
        tbsp: ['tbsp', 'tablespoon', 'tablespoons', 'tbs'],
        tsp: ['tsp', 'teaspoon', 'teaspoons'],
        g: ['g', 'gram', 'grams', 'gm'],
        oz: ['oz', 'ounce', 'ounces'],
        lb: ['lb', 'lbs', 'pound', 'pounds'],
        piece: ['piece', 'pieces', 'pc'],
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
        return null;
    }

    /** Parse recipe.unit_of_measurement with recipe.quantity from DB. */
    function parseCatalogUnit(unitStr, recipeQuantity) {
        const raw = (unitStr || '').trim();
        let catalogQuantity = recipeQuantity > 0 ? recipeQuantity : 1.0;
        let unitPart = raw;

        const leading = raw.match(/^(\d+(?:\.\d+)?)\s+(.+)$/);
        if (leading) {
            const n = parseFloat(leading[1]);
            if (!isNaN(n) && n > 0) {
                catalogQuantity = n;
                unitPart = leading[2].trim();
            }
        }

        const std = matchStandardUnit(unitPart);
        if (std) {
            return {
                catalogQuantity,
                catalogUnit: std,
                servingLabel: raw || std,
                foodSpecificServing: false,
            };
        }

        if (/^100\s*g$/i.test(raw)) {
            return {
                catalogQuantity: 100,
                catalogUnit: 'g',
                servingLabel: '100 g',
                foodSpecificServing: false,
            };
        }

        return {
            catalogQuantity,
            catalogUnit: 'serving',
            servingLabel: unitPart || 'serving',
            foodSpecificServing: true,
        };
    }

    function normalizeUnit(unit) {
        if (!unit || !String(unit).trim()) return 'piece';
        const parsed = parseCatalogUnit(String(unit).trim(), 1);
        if (!parsed.foodSpecificServing) return parsed.catalogUnit;
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

    function amountInCatalogUnits(item) {
        item.approximateCalories = false;
        const catalogQty = item.recipeQuantity > 0 ? item.recipeQuantity : 1.0;
        const catalogUnit = item.catalogUnit || 'serving';
        const qty = item.quantity > 0 ? item.quantity : 1.0;
        const displayUnit = normalizeUnit(item.unit || catalogUnit);

        if (item.foodSpecificServing) {
            if (displayUnit === 'serving' || COUNT_UNITS.includes(displayUnit)) {
                return qty * catalogQty;
            }
            if (getUnitCategory(displayUnit) === 'weight') {
                item.approximateCalories = true;
                const grams = convertUnit(qty, displayUnit, 'g');
                if (!isNaN(grams) && grams > 0 && item.gramsPerServing > 0) {
                    return (grams / item.gramsPerServing) * catalogQty;
                }
            }
            if (getUnitCategory(displayUnit) === 'volume') {
                item.approximateCalories = true;
                const cups = convertUnit(qty, displayUnit, 'cup');
                if (!isNaN(cups) && cups > 0) {
                    return cups * catalogQty;
                }
            }
            return NaN;
        }

        if (displayUnit === catalogUnit) {
            return qty;
        }

        if (canConvertUnits(displayUnit, catalogUnit)) {
            const converted = convertUnit(qty, displayUnit, catalogUnit);
            if (!isNaN(converted) && converted > 0) return converted;
        }

        return NaN;
    }

    function buildFeedingItem(opts) {
        const parsed = parseCatalogUnit(opts.unitRaw || '', opts.recipeQuantity || 1);
        const recipeQuantity = parsed.catalogQuantity;
        const catalogCalories = opts.calories > 0 ? opts.calories : 0;
        return {
            name: opts.name,
            calories: catalogCalories,
            recipeQuantity,
            catalogUnit: parsed.catalogUnit,
            servingLabel: parsed.servingLabel,
            foodSpecificServing: parsed.foodSpecificServing,
            originalRecipeUnit: parsed.foodSpecificServing ? 'serving' : parsed.catalogUnit,
            proteinPerCatalog: opts.proteinG != null ? opts.proteinG : 0,
            fiberPerCatalog: opts.fiberG != null ? opts.fiberG : 0,
            quantity: 1.0,
            unit: parsed.foodSpecificServing ? 'serving' : parsed.catalogUnit,
            source: opts.source || '',
            caloriesOverride: null,
            manualCalories: false,
            gramsPerServing:
                opts.gramsPerServing > 0
                    ? opts.gramsPerServing
                    : !parsed.foodSpecificServing && parsed.catalogUnit === 'g'
                      ? parsed.catalogQuantity
                      : 0,
            caloriesInvalid: false,
            crossUnitNote: false,
            totalCalories: catalogCalories,
            totalProtein: opts.proteinG || 0,
            totalFiber: opts.fiberG || 0,
        };
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
        const perCatalog = item.calories > 0 ? item.calories / catalogQty : 0;
        const qtyInCatalog = amountInCatalogUnits(item);

        if (isNaN(qtyInCatalog)) {
            item.caloriesInvalid = true;
            item.totalCalories = null;
            item.totalProtein = null;
            item.totalFiber = null;
            return 0;
        }

        item.caloriesInvalid = false;
        const displayUnit = normalizeUnit(item.unit);
        item.crossUnitNote =
            item.approximateCalories ||
            (displayUnit !== item.catalogUnit && !item.foodSpecificServing);

        item.totalCalories = Math.max(0, Math.round(perCatalog * qtyInCatalog));
        item.totalProtein = round1((item.proteinPerCatalog / catalogQty) * qtyInCatalog);
        item.totalFiber = round1((item.fiberPerCatalog / catalogQty) * qtyInCatalog);
        return item.totalCalories;
    }

    function round1(n) {
        return Math.round(n * 10) / 10;
    }

    global.FeedingNutrition = {
        ALL_FEEDING_UNITS: ['piece', 'serving', 'cup', 'g', 'oz', 'tbsp', 'tsp', 'slice', 'lb'],
        formatQuantity,
        parseCatalogUnit,
        normalizeUnit,
        getUnitCategory,
        canConvertUnits,
        convertUnit,
        amountInCatalogUnits,
        buildFeedingItem,
        recalculateItem,
    };
})(typeof window !== 'undefined' ? window : global);
