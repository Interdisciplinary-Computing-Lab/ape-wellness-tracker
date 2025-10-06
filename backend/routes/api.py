"""
API routes for researcher-grade data exports
"""

from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from backend.services.export_service import ExportService
from backend.models.export import ExportType, ExportFormat
from backend.extensions import db
from datetime import datetime
import os
from pathlib import Path

# Create API blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/exports', methods=['POST'])
@login_required
def create_export():
    """Create a new export job"""
    try:
        data = request.get_json()
        
        # Validate request data
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        # Validate export type
        if 'type' not in data or data['type'] not in ['raw', 'derived']:
            return jsonify({'error': 'type must be "raw" or "derived"'}), 400
        
        # Validate format
        if 'format' not in data or data['format'] not in ['csv_pack', 'parquet', 'sqlite', 'jsonl_pack']:
            return jsonify({'error': 'format must be one of: csv_pack, parquet, sqlite, jsonl_pack'}), 400
        
        # For now, return a simple success response to test the frontend
        import uuid
        job_id = str(uuid.uuid4())
        
        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'download_url': f'/api/v1/exports/{job_id}/download'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error creating export: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/exports/<job_id>', methods=['GET'])
@login_required
def get_export_status(job_id):
    """Get export job status"""
    try:
        service = ExportService()
        job_status = service.get_job_status(job_id)
        
        if not job_status:
            return jsonify({'error': 'Export job not found'}), 404
        
        # Check if user owns this job
        if job_status.get('user_id') != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        return jsonify(job_status), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting export status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/exports/<job_id>/download', methods=['GET'])
@login_required
def download_export(job_id):
    """Download completed export file"""
    try:
        service = ExportService()
        job_status = service.get_job_status(job_id)
        
        if not job_status:
            return jsonify({'error': 'Export job not found'}), 404
        
        # Check if user owns this job
        if job_status.get('user_id') != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Check if job is completed
        if job_status['status'] != 'completed':
            return jsonify({'error': 'Export not ready'}), 400
        
        # Get file path
        file_path = Path(service.temp_dir) / f"export_{job_id}.zip"
        
        if not file_path.exists():
            return jsonify({'error': 'Export file not found'}), 404
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"bonobo_export_{job_id}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading export: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/metadata/schema', methods=['GET'])
@login_required
def get_schema():
    """Get database schema metadata"""
    try:
        schema = {
            "schema_version": "1.2",
            "tables": [
                {
                    "name": "Ape_Information",
                    "columns": [
                        {"name": "ape_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "name", "type": "text", "units": None, "nullable": False},
                        {"name": "birth_date", "type": "date", "units": "ISO-8601", "nullable": True},
                        {"name": "weight_kg", "type": "decimal", "units": "kg", "nullable": True},
                        {"name": "mother", "type": "text", "units": None, "nullable": True},
                        {"name": "image_filename", "type": "text", "units": None, "nullable": True},
                        {"name": "image_mime_type", "type": "text", "units": None, "nullable": True},
                        {"name": "is_archived", "type": "boolean", "units": None, "nullable": False},
                        {"name": "archived_at", "type": "timestamp", "units": "ISO-8601", "nullable": True}
                    ]
                },
                {
                    "name": "Meal_Logs",
                    "columns": [
                        {"name": "meal_log_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "ape_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "recipe_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "meal_time", "type": "datetime", "units": "ISO-8601", "nullable": False},
                        {"name": "user_id", "type": "integer", "units": None, "nullable": True}
                    ]
                },
                {
                    "name": "Meal_Definitions",
                    "columns": [
                        {"name": "recipe_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "meal_name", "type": "text", "units": None, "nullable": False},
                        {"name": "description", "type": "text", "units": None, "nullable": True},
                        {"name": "calories", "type": "decimal", "units": "kcal", "nullable": False},
                        {"name": "food_category", "type": "text", "units": None, "nullable": True},
                        {"name": "category_id", "type": "integer", "units": None, "nullable": True}
                    ]
                },
                {
                    "name": "Food_Categories",
                    "columns": [
                        {"name": "category_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "name", "type": "text", "units": None, "nullable": False},
                        {"name": "description", "type": "text", "units": None, "nullable": True},
                        {"name": "icon", "type": "text", "units": None, "nullable": True},
                        {"name": "color", "type": "text", "units": None, "nullable": True},
                        {"name": "is_active", "type": "boolean", "units": None, "nullable": False},
                        {"name": "sort_order", "type": "integer", "units": None, "nullable": False},
                        {"name": "created_at", "type": "timestamp", "units": "ISO-8601", "nullable": True},
                        {"name": "updated_at", "type": "timestamp", "units": "ISO-8601", "nullable": True}
                    ]
                },
                {
                    "name": "Derived_Meal_Metrics",
                    "columns": [
                        {"name": "meal_log_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "ape_id", "type": "integer", "units": None, "nullable": False},
                        {"name": "age_at_meal_days", "type": "integer", "units": "days", "nullable": False},
                        {"name": "calories_total", "type": "decimal", "units": "kcal", "nullable": False},
                        {"name": "calories_per_kg", "type": "decimal", "units": "kcal/kg", "nullable": True},
                        {"name": "weight_kg_at_meal", "type": "decimal", "units": "kg", "nullable": True}
                    ]
                }
            ]
        }
        
        return jsonify(schema), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting schema: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/metadata/apes', methods=['GET'])
@login_required
def get_apes_metadata():
    """Get list of available apes for filtering"""
    try:
        from backend.models.entry import Apes
        
        apes = Apes.query.filter_by(is_archived=False).all()
        
        ape_data = [
            {
                'id': ape.id,
                'name': ape.ape_name,
                'birth_date': ape.birthday.isoformat() if ape.birthday else None,
                'weight_kg': ape.weight
            }
            for ape in apes
        ]
        
        return jsonify({'apes': ape_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting apes metadata: {e}")
        # Return empty list on error for now
        return jsonify({'apes': []}), 200

@api.route('/metadata/categories', methods=['GET'])
@login_required
def get_categories_metadata():
    """Get list of available food categories for filtering"""
    try:
        from backend.models.entry import FoodCategory
        
        categories = FoodCategory.query.filter_by(is_active=True).all()
        
        category_data = [
            {
                'id': category.id,
                'name': category.name,
                'description': category.description
            }
            for category in categories
        ]
        
        return jsonify({'categories': category_data}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting categories metadata: {e}")
        # Return empty list on error for now
        return jsonify({'categories': []}), 200
