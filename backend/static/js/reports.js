function getDateFilterForm() {
    return document.getElementById('dateFilterForm');
}

function getFilterParams() {
    const form = getDateFilterForm();
    if (!form) {
        return { range: 'today', date: '', start_date: '', end_date: '' };
    }

    const rangeEl = form.querySelector('[name="range"]');
    const dateEl = form.querySelector('[name="date"]');
    const startEl = form.querySelector('[name="start_date"]');
    const endEl = form.querySelector('[name="end_date"]');

    return {
        range: rangeEl ? rangeEl.value : 'today',
        date: dateEl ? dateEl.value : '',
        start_date: startEl ? startEl.value : '',
        end_date: endEl ? endEl.value : '',
    };
}

function validateFilterParams(params) {
    if (params.range === 'custom' && !params.date) {
        alert('Please choose a date from the calendar.');
        return false;
    }
    if (params.range === 'custom_range' && (!params.start_date || !params.end_date)) {
        alert('Please choose both a start date and an end date from the calendar.');
        return false;
    }
    return true;
}

function buildQueryString(params) {
    const search = new URLSearchParams();
    search.set('range', params.range || 'today');
    if (params.date) {
        search.set('date', params.date);
    }
    if (params.start_date) {
        search.set('start_date', params.start_date);
    }
    if (params.end_date) {
        search.set('end_date', params.end_date);
    }
    return search.toString();
}

function buildCsvDownloadUrl() {
    const btn = document.querySelector('.download-csv-btn');
    const baseUrl = btn ? btn.getAttribute('data-base-url') : '';
    if (!baseUrl) {
        return '';
    }
    const params = getFilterParams();
    if (!validateFilterParams(params)) {
        return '';
    }
    return baseUrl + '?' + buildQueryString(params);
}

function buildRawDownloadUrl() {
    const btn = document.querySelector('.download-raw-btn');
    const baseUrl = btn ? btn.getAttribute('data-action') : '';
    if (!baseUrl) {
        return '';
    }
    const params = getFilterParams();
    if (!validateFilterParams(params)) {
        return '';
    }
    const denormalizedEl = document.getElementById('denormalizedCheck');
    const search = new URLSearchParams(buildQueryString(params));
    search.set(
        'denormalized',
        denormalizedEl && denormalizedEl.checked ? 'true' : 'false'
    );
    return baseUrl + '?' + search.toString();
}

function triggerFileDownload(url) {
    if (!url) {
        return;
    }
    window.location.href = url;
}

function openDatePicker(input) {
    if (!input) {
        return;
    }
    input.focus();
    if (typeof input.showPicker === 'function') {
        try {
            input.showPicker();
        } catch (err) {
            // Some browsers block showPicker without a direct user gesture.
        }
    }
}

function updateCustomDateVisibility(openPicker) {
    const rangeSelect = document.getElementById('range');
    const customDateGroup = document.getElementById('customDateGroup');
    const customRangeGroup = document.getElementById('customRangeGroup');
    const dateInput = document.getElementById('date');
    const startDateInput = document.getElementById('start_date');

    if (!rangeSelect || !customDateGroup || !customRangeGroup) {
        return rangeSelect ? rangeSelect.value : '';
    }

    customDateGroup.style.display = 'none';
    customRangeGroup.style.display = 'none';

    if (rangeSelect.value === 'custom') {
        customDateGroup.style.display = 'block';
        if (openPicker) {
            setTimeout(function() {
                openDatePicker(dateInput);
            }, 150);
        }
    } else if (rangeSelect.value === 'custom_range') {
        customRangeGroup.style.display = 'block';
        if (openPicker) {
            setTimeout(function() {
                openDatePicker(startDateInput);
            }, 150);
        }
    }

    return rangeSelect.value;
}

function submitDateFilterForm() {
    const dateFilterForm = getDateFilterForm();
    if (dateFilterForm) {
        dateFilterForm.submit();
    }
}

function onRangeSelectChange() {
    const range = updateCustomDateVisibility(true);
    if (range !== 'custom' && range !== 'custom_range') {
        submitDateFilterForm();
    }
}

function handleDateChange() {
    setTimeout(submitDateFilterForm, 100);
}

function handleStartDateChange() {
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    if (!startInput || !endInput || !startInput.value) {
        return;
    }

    if (!endInput.value || startInput.value > endInput.value) {
        endInput.value = startInput.value;
    }

    setTimeout(submitDateFilterForm, 100);
}

function handleEndDateChange() {
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');

    if (startInput && endInput && startInput.value && endInput.value) {
        setTimeout(submitDateFilterForm, 100);
    }
}

function closeMobileSidebar() {
    document.body.classList.remove('sidebar-open', 'sidebar-is-opening');
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
        overlay.remove();
    }
}

function initializeDownloadButtons() {
    document.querySelectorAll('.progress-bar[data-width]').forEach(function(bar) {
        bar.style.width = bar.getAttribute('data-width') + '%';
    });

    updateCustomDateVisibility(false);
    closeMobileSidebar();

    const dateInput = document.getElementById('date');
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    if (dateInput) {
        dateInput.addEventListener('change', handleDateChange);
    }
    if (startDateInput) {
        startDateInput.addEventListener('change', handleStartDateChange);
    }
    if (endDateInput) {
        endDateInput.addEventListener('change', handleEndDateChange);
    }

    document.querySelectorAll('.download-csv-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            triggerFileDownload(buildCsvDownloadUrl());
        });
    });

    document.querySelectorAll('.download-raw-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            triggerFileDownload(buildRawDownloadUrl());
        });
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeDownloadButtons);
} else {
    initializeDownloadButtons();
}

document.addEventListener('click', function(e) {
    if (!document.body.classList.contains('sidebar-open')) {
        return;
    }
    if (e.target.closest('.main-sidebar') || e.target.closest('[data-widget="pushmenu"]')) {
        return;
    }
    closeMobileSidebar();
});
