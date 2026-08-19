"""
Reports and data export routes for the Ape Wellness Tracker application.
"""

import io
import os
import shutil
import sys
import tempfile
import traceback
import zipfile
from datetime import datetime

from flask import flash, redirect, render_template, request, send_file, url_for
from flask_security import login_required
from backend.utils.authz import export_required

from backend.models.entry import Apes
from backend.routes import site
from backend.utils.report_aggregates import build_report_aggregates
from backend.utils.report_date_range import (
    calculate_date_range,
    get_meals_in_range,
    parse_export_date_range,
)
from backend.utils.report_generators import (
    generate_group_and_category_breakdown,
    generate_individual_summary,
)
from backend.utils.report_utils import generate_csv_report
from backend.utils.raw_data_export import build_raw_data_zip


def _zip_download_response(zip_buffer, filename, mimetype='application/zip'):
    response = send_file(
        zip_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype,
    )
    response.headers['Content-Disposition'] = (
        f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}'
    )
    response.headers['Content-Type'] = mimetype
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@site.route('/reports')
@login_required
def reports():
    """Display aggregate reports for all apes."""
    start_date, end_date, date_range, custom_date, custom_start_date, custom_end_date = (
        calculate_date_range()
    )
    apes = Apes.query.all()
    meals_in_range = get_meals_in_range(start_date, end_date)
    (
        total_calories,
        total_meals,
        avg_calories_per_meal,
        ape_stats,
        category_data,
        daily_data,
        meal_type_totals,
    ) = build_report_aggregates(meals_in_range, apes)

    return render_template(
        'reports.html',
        apes=apes,
        ape_stats=ape_stats,
        total_calories=total_calories,
        total_meals=total_meals,
        avg_calories_per_meal=avg_calories_per_meal,
        category_data=category_data,
        daily_data=daily_data,
        meal_type_totals=meal_type_totals,
        date_range=date_range,
        start_date=start_date,
        end_date=end_date,
        custom_date=custom_date,
        custom_start_date=custom_start_date,
        custom_end_date=custom_end_date,
    )


@site.route('/reports/download/<format>')
@login_required
@export_required
def download_reports(format):
    """Download meal reports data in CSV format."""
    start_date, end_date, _, _, _, _ = calculate_date_range()
    meals_in_range = get_meals_in_range(start_date, end_date)
    apes = Apes.query.all()
    (
        total_calories,
        total_meals,
        avg_calories_per_meal,
        ape_stats,
        category_data,
        daily_data,
        meal_type_totals,
    ) = build_report_aggregates(meals_in_range, apes, for_download=True)

    filename_date_range = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"

    if format.lower() == 'csv':
        return generate_csv_report(
            filename_date_range,
            apes,
            ape_stats,
            category_data,
            daily_data,
            total_calories,
            total_meals,
            avg_calories_per_meal,
            start_date,
            end_date,
            meal_type_totals,
        )

    flash('Invalid download format. Please choose CSV.', 'error')
    return redirect(url_for('site.reports'))


@site.route('/reports/download/raw', methods=['GET'])
@login_required
@export_required
def download_raw_data():
    """Download raw database data as CSV files in a zip archive."""
    try:
        include_denormalized = request.args.get('denormalized', 'false').lower() == 'true'
        start_date, end_date = parse_export_date_range()
        zip_buffer, filename = build_raw_data_zip(
            start_date, end_date, include_denormalized=include_denormalized
        )
        return _zip_download_response(zip_buffer, filename)
    except Exception as e:
        print(f'Error in download_raw_data: {e}', file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        flash(f'Error generating raw data download: {e}', 'error')
        return redirect(url_for('site.reports'))


@site.route('/reports/download/excel', methods=['GET'])
@login_required
@export_required
def download_excel_reports():
    """Download Excel reports (Individual Summary and Group Breakdown)."""
    try:
        start_date, end_date, _, _, _, _ = calculate_date_range()
        temp_dir = tempfile.mkdtemp()
        try:
            individual_file = os.path.join(temp_dir, 'Bonobo_Individual_Diet_Summary.xlsx')
            group_file = os.path.join(temp_dir, 'Bonobo_Group_And_Category_Breakdown.xlsx')

            generate_individual_summary(individual_file, start_date, end_date)
            generate_group_and_category_breakdown(group_file, start_date, end_date)

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                if os.path.exists(individual_file):
                    zip_file.write(individual_file, 'Bonobo_Individual_Diet_Summary.xlsx')
                if os.path.exists(group_file):
                    zip_file.write(group_file, 'Bonobo_Group_And_Category_Breakdown.xlsx')

            zip_buffer.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            if start_date == end_date:
                date_suffix = f"_{start_date.strftime('%Y%m%d')}"
            else:
                date_suffix = f"_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
            filename = f'bonobo_diet_reports{date_suffix}_{timestamp}.zip'
            return _zip_download_response(zip_buffer, filename)
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(
                    f'Warning: Failed to cleanup temp directory {temp_dir}: {cleanup_error}',
                    file=sys.stderr,
                )
    except Exception as e:
        print(f'Error in download_excel_reports: {e}', file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        flash(f'Error generating Excel reports: {e}', 'error')
        return redirect(url_for('site.reports'))
