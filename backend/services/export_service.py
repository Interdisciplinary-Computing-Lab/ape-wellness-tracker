"""
Export service for researcher-grade data exports
"""

import os
import io
import csv
import json
import sqlite3
import zipfile
import hashlib
import tempfile
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
# import pandas as pd  # Commented out for now - will implement CSV export without pandas
from sqlalchemy import text
from backend.extensions import db
from backend.models.entry import Apes, Meals, Recipe, FoodCategory, User
from backend.models.export import (
    ExportAudit, ExportType, ExportFormat, ExportStatus, 
    ExportFilters, ValidationReport, ExportManifest
)
from flask import current_app
import threading
import queue
import time

class ExportWorker:
    """Background worker for processing export jobs"""
    
    def __init__(self):
        self.job_queue = queue.Queue()
        self.running = False
        self.worker_thread = None
    
    def start(self):
        """Start the worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """Stop the worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()
    
    def enqueue_job(self, job_id: str):
        """Add job to queue"""
        self.job_queue.put(job_id)
    
    def _worker_loop(self):
        """Main worker loop"""
        while self.running:
            try:
                job_id = self.job_queue.get(timeout=1)
                self._process_job(job_id)
                self.job_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                current_app.logger.error(f"Worker error: {e}")
    
    def _process_job(self, job_id: str):
        """Process a single export job"""
        try:
            with current_app.app_context():
                job = ExportAudit.query.filter_by(job_id=job_id).first()
                if not job:
                    return
                
                # Update status to running
                job.status = ExportStatus.RUNNING.value
                job.started_at = datetime.utcnow()
                job.progress = 10
                db.session.commit()
                
                # Create export service and process
                service = ExportService()
                result = service.process_export(job)
                
                if result['success']:
                    job.status = ExportStatus.COMPLETED.value
                    job.download_url = result['download_url']
                    job.row_counts = result['row_counts']
                else:
                    job.status = ExportStatus.FAILED.value
                    job.error_message = result['error']
                
                job.finished_at = datetime.utcnow()
                job.progress = 100
                db.session.commit()
                
        except Exception as e:
            current_app.logger.error(f"Job processing error: {e}")
            with current_app.app_context():
                job = ExportAudit.query.filter_by(job_id=job_id).first()
                if job:
                    job.status = ExportStatus.FAILED.value
                    job.error_message = str(e)
                    job.finished_at = datetime.utcnow()
                    db.session.commit()

# Global worker instance
export_worker = ExportWorker()

class ExportService:
    """Service for handling data exports"""
    
    def __init__(self):
        self.temp_dir = os.getenv('EXPORT_TEMP_DIR', '/tmp/exports')
        self.url_ttl = int(os.getenv('EXPORT_SIGNED_URL_TTL', '3600'))
        self.hash_salt = os.getenv('EXPORT_HASH_SALT', 'default_salt_change_in_production')
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def create_export_job(self, user_id: int, request_data: Dict[str, Any]) -> str:
        """Create a new export job"""
        try:
            # Parse request data
            export_type = ExportType(request_data['type'])
            export_format = ExportFormat(request_data['format'])
            filters = ExportFilters.from_dict(request_data['filters'])
            
            # Create job record
            job_id = str(uuid.uuid4())
            job = ExportAudit(
                user_id=user_id,
                type=export_type.value,
                format=export_format.value,
                filters=filters,
                job_id=job_id,
                status=ExportStatus.QUEUED.value
            )
            
            db.session.add(job)
            db.session.commit()
            
            # Process immediately for now (instead of background worker)
            # export_worker.enqueue_job(job_id)
            # For now, we'll process synchronously
            pass
            
            return job_id
            
        except Exception as e:
            current_app.logger.error(f"Error creating export job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        job = ExportAudit.query.filter_by(job_id=job_id).first()
        return job.to_dict() if job else None
    
    def process_export(self, job: ExportAudit) -> Dict[str, Any]:
        """Process export job and generate files"""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory(dir=self.temp_dir) as temp_dir:
                temp_path = Path(temp_dir)
                
                # Create export directory structure
                export_dir = temp_path / f"bonobo_export_{job.type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                data_dir = export_dir / "data"
                metadata_dir = export_dir / "metadata"
                examples_dir = export_dir / "examples"
                
                for dir_path in [data_dir, metadata_dir, examples_dir]:
                    dir_path.mkdir(parents=True, exist_ok=True)
                
                # Parse filters
                filters = ExportFilters.from_dict(job.filters)
                
                # Export data files
                table_counts = {}
                table_checksums = {}
                
                job.progress = 20
                db.session.commit()
                
                # Export main tables
                tables_to_export = [
                    ('Ape_Information', self._export_apes, filters),
                    ('Meal_Logs', self._export_meals, filters),
                    ('Meal_Definitions', self._export_recipes, filters),
                    ('Food_Categories', self._export_categories, filters)
                ]
                
                if job.type == ExportType.DERIVED.value or filters.include_calculated:
                    tables_to_export.append(('Derived_Meal_Metrics', self._export_derived_metrics, filters))
                
                for table_name, export_func, export_filters in tables_to_export:
                    count, checksum = export_func(data_dir, table_name, export_filters, job.format)
                    table_counts[table_name] = count
                    table_checksums[table_name] = checksum
                
                job.progress = 60
                db.session.commit()
                
                # Generate metadata files
                self._generate_manifest(metadata_dir, job, filters, table_counts, table_checksums)
                self._generate_data_dictionary(metadata_dir)
                self._generate_schema(metadata_dir)
                self._generate_datapackage(metadata_dir, table_counts)
                self._generate_examples(examples_dir)
                self._generate_readme(export_dir)
                
                job.progress = 80
                db.session.commit()
                
                # Run validation
                validation_report = self._run_validation(data_dir, table_counts)
                self._write_validation_report(metadata_dir, validation_report)
                
                job.progress = 90
                db.session.commit()
                
                # Create zip file
                zip_path = temp_path / f"export_{job.job_id}.zip"
                self._create_zip_file(export_dir, zip_path)
                
                # Move to permanent location and generate signed URL
                final_path = Path(self.temp_dir) / f"export_{job.job_id}.zip"
                shutil.move(str(zip_path), str(final_path))
                
                # Generate signed URL (simplified - in production use proper signing)
                download_url = f"/api/v1/exports/{job.job_id}/download"
                
                return {
                    'success': True,
                    'download_url': download_url,
                    'row_counts': table_counts
                }
                
        except Exception as e:
            current_app.logger.error(f"Export processing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _export_apes(self, data_dir: Path, table_name: str, filters: ExportFilters, format: str) -> Tuple[int, str]:
        """Export apes data"""
        query = db.session.query(Apes)
        
        # Apply filters
        if filters.ape_ids:
            query = query.filter(Apes.id.in_(filters.ape_ids))
        
        apes = query.all()
        
        # Prepare data
        data = []
        for ape in apes:
            row = {
                'ape_id': ape.id,
                'name': ape.ape_name,
                'birth_date': ape.birthday.isoformat() if ape.birthday else None,
                'weight_kg': ape.weight,
                'mother': ape.mother,
                'image_filename': ape.image_filename,
                'image_mime_type': ape.image_mime_type,
                'is_archived': ape.is_archived,
                'archived_at': ape.archived_at.isoformat() if ape.archived_at else None
            }
            
            # Handle privacy settings
            if not filters.include_identifiers:
                row['name'] = self._hash_identifier(ape.ape_name)
                if row['birth_date']:
                    # Round birth date to month for privacy
                    birth_date = datetime.fromisoformat(row['birth_date'].replace('Z', '+00:00'))
                    row['birth_date'] = birth_date.replace(day=1).isoformat()
            
            data.append(row)
        
        return self._write_data_file(data_dir, table_name, data, format)
    
    def _export_meals(self, data_dir: Path, table_name: str, filters: ExportFilters, format: str) -> Tuple[int, str]:
        """Export meals data"""
        query = db.session.query(Meals)
        
        # Apply filters
        if filters.ape_ids:
            query = query.filter(Meals.ape_id.in_(filters.ape_ids))
        if filters.date_from:
            query = query.filter(Meals.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(Meals.date <= filters.date_to)
        
        meals = query.all()
        
        # Prepare data
        data = []
        for meal in meals:
            row = {
                'meal_log_id': meal.id,
                'ape_id': meal.ape_id,
                'recipe_id': meal.recipe_id,
                'meal_time': meal.date.isoformat() if meal.date else None,
                'user_id': meal.user_id
            }
            
            # Handle privacy settings
            if not filters.include_identifiers:
                row['user_id'] = self._hash_identifier(str(meal.user_id))
            
            data.append(row)
        
        return self._write_data_file(data_dir, table_name, data, format)
    
    def _export_recipes(self, data_dir: Path, table_name: str, filters: ExportFilters, format: str) -> Tuple[int, str]:
        """Export recipes data"""
        query = db.session.query(Recipe)
        
        # Apply filters
        if filters.food_category_ids:
            query = query.filter(Recipe.category_id.in_(filters.food_category_ids))
        
        recipes = query.all()
        
        # Prepare data
        data = []
        for recipe in recipes:
            row = {
                'recipe_id': recipe.id,
                'meal_name': recipe.meal_name,
                'description': recipe.description,
                'calories': recipe.calories,
                'food_category': recipe.food_category,
                'category_id': recipe.category_id
            }
            data.append(row)
        
        return self._write_data_file(data_dir, table_name, data, format)
    
    def _export_categories(self, data_dir: Path, table_name: str, filters: ExportFilters, format: str) -> Tuple[int, str]:
        """Export food categories data"""
        query = db.session.query(FoodCategory)
        
        # Apply filters
        if filters.food_category_ids:
            query = query.filter(FoodCategory.id.in_(filters.food_category_ids))
        
        categories = query.all()
        
        # Prepare data
        data = []
        for category in categories:
            row = {
                'category_id': category.id,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'color': category.color,
                'is_active': category.is_active,
                'sort_order': category.sort_order,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None
            }
            data.append(row)
        
        return self._write_data_file(data_dir, table_name, data, format)
    
    def _export_derived_metrics(self, data_dir: Path, table_name: str, filters: ExportFilters, format: str) -> Tuple[int, str]:
        """Export derived metrics"""
        # This is a simplified implementation - would need more complex calculations
        query = db.session.query(Meals).join(Apes).join(Recipe)
        
        # Apply filters
        if filters.ape_ids:
            query = query.filter(Meals.ape_id.in_(filters.ape_ids))
        if filters.date_from:
            query = query.filter(Meals.date >= filters.date_from)
        if filters.date_to:
            query = query.filter(Meals.date <= filters.date_to)
        
        meals = query.all()
        
        # Calculate derived metrics
        data = []
        for meal in meals:
            age_at_meal = None
            if meal.ape.birthday and meal.date:
                age_at_meal = (meal.date.date() - meal.ape.birthday).days
            
            calories_per_kg = None
            if meal.ape.weight and meal.ape.weight > 0:
                calories_per_kg = meal.recipe.calories / meal.ape.weight
            
            row = {
                'meal_log_id': meal.id,
                'ape_id': meal.ape_id,
                'age_at_meal_days': age_at_meal,
                'calories_total': meal.recipe.calories,
                'calories_per_kg': calories_per_kg,
                'weight_kg_at_meal': meal.ape.weight
            }
            data.append(row)
        
        return self._write_data_file(data_dir, table_name, data, format)
    
    def _write_data_file(self, data_dir: Path, table_name: str, data: List[Dict], format: str) -> Tuple[int, str]:
        """Write data to file in specified format"""
        if not data:
            return 0, ""
        
        if format == ExportFormat.CSV_PACK.value:
            file_path = data_dir / f"{table_name}.csv"
            self._write_csv_file(file_path, data)
        elif format == ExportFormat.PARQUET.value:
            # For now, fall back to CSV since pandas is commented out
            file_path = data_dir / f"{table_name}.csv"
            self._write_csv_file(file_path, data)
        elif format == ExportFormat.JSONL_PACK.value:
            file_path = data_dir / f"{table_name}.jsonl"
            self._write_jsonl_file(file_path, data)
        else:
            # Default to CSV
            file_path = data_dir / f"{table_name}.csv"
            self._write_csv_file(file_path, data)
        
        # Calculate checksum
        with open(file_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        return len(data), checksum
    
    def _write_csv_file(self, file_path: Path, data: List[Dict]):
        """Write data to CSV file"""
        if not data:
            return
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    
    def _write_jsonl_file(self, file_path: Path, data: List[Dict]):
        """Write data to JSONL file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for row in data:
                f.write(json.dumps(row) + '\n')
    
    def _hash_identifier(self, identifier: str) -> str:
        """Hash identifier for privacy"""
        return hashlib.sha256((self.hash_salt + str(identifier)).encode()).hexdigest()[:16]
    
    def _generate_manifest(self, metadata_dir: Path, job: ExportAudit, filters: ExportFilters, 
                          table_counts: Dict[str, int], table_checksums: Dict[str, str]):
        """Generate export manifest"""
        manifest = ExportManifest(job.type, job.format, filters, table_counts, table_checksums)
        
        with open(metadata_dir / "manifest.json", 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
    
    def _generate_data_dictionary(self, metadata_dir: Path):
        """Generate data dictionary CSV"""
        dictionary_data = [
            ['table', 'column', 'type', 'description', 'units', 'nullable', 'allowed_values'],
            ['Ape_Information', 'ape_id', 'integer', 'Primary key', '', 'false', ''],
            ['Ape_Information', 'name', 'text', 'Ape name', '', 'false', ''],
            ['Ape_Information', 'birth_date', 'date', 'Birthdate', 'ISO-8601', 'true', ''],
            ['Ape_Information', 'weight_kg', 'decimal', 'Weight in kilograms', 'kg', 'true', ''],
            ['Meal_Logs', 'meal_log_id', 'integer', 'Primary key', '', 'false', ''],
            ['Meal_Logs', 'ape_id', 'integer', 'FK→Ape_Information.ape_id', '', 'false', ''],
            ['Meal_Logs', 'recipe_id', 'integer', 'FK→Meal_Definitions.recipe_id', '', 'false', ''],
            ['Meal_Logs', 'meal_time', 'datetime', 'UTC timestamp', 'ISO-8601', 'false', ''],
            ['Meal_Definitions', 'calories', 'decimal', 'Calories per serving', 'kcal', 'false', ''],
            ['Food_Categories', 'name', 'text', 'Category label', '', 'false', ''],
            ['Derived_Meal_Metrics', 'age_at_meal_days', 'integer', 'Age on meal day', 'days', 'false', ''],
            ['Derived_Meal_Metrics', 'calories_per_kg', 'decimal', 'Calories/body_mass', 'kcal/kg', 'true', '']
        ]
        
        with open(metadata_dir / "data_dictionary.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(dictionary_data)
    
    def _generate_schema(self, metadata_dir: Path):
        """Generate SQL schema"""
        schema_sql = """
-- Ape Wellness Tracker Database Schema
-- Generated: {timestamp}

CREATE TABLE Ape_Information (
    ape_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    birth_date DATE,
    weight_kg DECIMAL,
    mother TEXT,
    image_filename TEXT,
    image_mime_type TEXT,
    is_archived BOOLEAN DEFAULT FALSE,
    archived_at TIMESTAMP
);

CREATE TABLE Meal_Logs (
    meal_log_id INTEGER PRIMARY KEY,
    ape_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    meal_time TIMESTAMP NOT NULL,
    user_id INTEGER,
    FOREIGN KEY (ape_id) REFERENCES Ape_Information(ape_id),
    FOREIGN KEY (recipe_id) REFERENCES Meal_Definitions(recipe_id)
);

CREATE TABLE Meal_Definitions (
    recipe_id INTEGER PRIMARY KEY,
    meal_name TEXT NOT NULL,
    description TEXT,
    calories DECIMAL NOT NULL,
    food_category TEXT,
    category_id INTEGER
);

CREATE TABLE Food_Categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    color TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

PRAGMA foreign_keys=ON;
        """.format(timestamp=datetime.utcnow().isoformat())
        
        with open(metadata_dir / "schema.sql", 'w') as f:
            f.write(schema_sql)
    
    def _generate_datapackage(self, metadata_dir: Path, table_counts: Dict[str, int]):
        """Generate Frictionless Data Package descriptor"""
        resources = []
        for table_name in table_counts.keys():
            resources.append({
                "name": table_name,
                "path": f"../data/{table_name}.csv",
                "format": "csv"
            })
        
        datapackage = {
            "profile": "tabular-data-package",
            "name": "bonobo_export",
            "resources": resources,
            "licenses": [{"name": "CC-BY-4.0"}]
        }
        
        with open(metadata_dir / "datapackage.json", 'w') as f:
            json.dump(datapackage, f, indent=2)
    
    def _generate_examples(self, examples_dir: Path):
        """Generate example scripts"""
        # Python example
        python_example = '''import pandas as pd
import json

# Load data
apes = pd.read_csv('data/Ape_Information.csv')
meals = pd.read_csv('data/Meal_Logs.csv')
recipes = pd.read_csv('data/Meal_Definitions.csv')

# Example analysis
print(f"Total apes: {len(apes)}")
print(f"Total meals: {len(meals)}")

# Join data for analysis
meal_analysis = meals.merge(apes, left_on='ape_id', right_on='ape_id', how='left')
meal_analysis = meal_analysis.merge(recipes, left_on='recipe_id', right_on='recipe_id', how='left')

# Calculate daily calories per ape
daily_calories = meal_analysis.groupby(['ape_id', 'name', meal_analysis['meal_time'].str[:10]])['calories'].sum()
print(daily_calories.head())
'''
        
        with open(examples_dir / "read_in_pandas.py", 'w') as f:
            f.write(python_example)
        
        # R example
        r_example = '''library(readr)
library(dplyr)

# Load data
apes <- read_csv('data/Ape_Information.csv')
meals <- read_csv('data/Meal_Logs.csv')
recipes <- read_csv('data/Meal_Definitions.csv')

# Example analysis
cat("Total apes:", nrow(apes), "\\n")
cat("Total meals:", nrow(meals), "\\n")

# Join data for analysis
meal_analysis <- meals %>%
  left_join(apes, by = 'ape_id') %>%
  left_join(recipes, by = 'recipe_id')

# Calculate daily calories per ape
daily_calories <- meal_analysis %>%
  mutate(date = as.Date(substr(meal_time, 1, 10))) %>%
  group_by(ape_id, name, date) %>%
  summarise(total_calories = sum(calories), .groups = 'drop')

print(head(daily_calories))
'''
        
        with open(examples_dir / "read_in_R.R", 'w') as f:
            f.write(r_example)
    
    def _generate_readme(self, export_dir: Path):
        """Generate README file"""
        readme_content = '''# Bonobo Feeding Log Export

This export contains raw data from the Ape Wellness Tracker system.

## Files

- `data/` - Data files in the requested format
- `metadata/` - Schema, validation, and documentation
- `examples/` - Sample code for loading data

## Data Description

- **Ape_Information**: Individual bonobo records
- **Meal_Logs**: Feeding events with timestamps
- **Meal_Definitions**: Recipe and nutritional information
- **Food_Categories**: Food classification system
- **Derived_Meal_Metrics**: Calculated metrics (if included)

## Privacy

All timestamps are in UTC. Researcher identifiers are hashed unless explicitly requested otherwise.

## Usage

See the examples/ directory for sample code to load and analyze the data in Python or R.

## Support

For questions about this export, contact the research team.
'''
        
        with open(export_dir / "README.txt", 'w') as f:
            f.write(readme_content)
    
    def _run_validation(self, data_dir: Path, table_counts: Dict[str, int]) -> ValidationReport:
        """Run data validation checks"""
        report = ValidationReport()
        
        try:
            # Basic validation - check file existence and row counts
            for table_name, expected_count in table_counts.items():
                file_path = data_dir / f"{table_name}.csv"
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        actual_count = sum(1 for line in f) - 1  # Subtract header
                    
                    if actual_count != expected_count:
                        report.row_count_mismatches[table_name] = f"Expected {expected_count}, got {actual_count}"
                else:
                    report.add_error("file", f"Missing file: {file_path}")
            
            # Basic FK integrity check using database queries
            try:
                # Check if all meal ape_ids exist in apes
                invalid_ape_ids = db.session.execute(text("""
                    SELECT COUNT(*) FROM meals m 
                    LEFT JOIN apes a ON m.ape_id = a.id 
                    WHERE a.id IS NULL
                """)).scalar()
                report.fk_integrity_errors += invalid_ape_ids or 0
                
                # Check if all meal recipe_ids exist in recipes
                invalid_recipe_ids = db.session.execute(text("""
                    SELECT COUNT(*) FROM meals m 
                    LEFT JOIN recipe r ON m.recipe_id = r.id 
                    WHERE r.id IS NULL
                """)).scalar()
                report.fk_integrity_errors += invalid_recipe_ids or 0
                
            except Exception as e:
                report.add_error("fk_check", f"FK validation error: {e}")
            
            # Basic temporal check
            try:
                future_meals = db.session.execute(text("""
                    SELECT COUNT(*) FROM meals 
                    WHERE date > datetime('now')
                """)).scalar()
                report.temporal_anomalies += future_meals or 0
            except Exception as e:
                report.add_error("temporal_check", f"Temporal validation error: {e}")
            
            # Basic null check
            try:
                null_names = db.session.execute(text("""
                    SELECT COUNT(*) FROM apes 
                    WHERE ape_name IS NULL OR ape_name = ''
                """)).scalar()
                if null_names > 0:
                    report.null_violations['Ape_Information.name'] = null_names
            except Exception as e:
                report.add_error("null_check", f"Null validation error: {e}")
            
            # Basic unit check
            try:
                negative_calories = db.session.execute(text("""
                    SELECT COUNT(*) FROM recipe 
                    WHERE calories < 0
                """)).scalar()
                report.unit_violations += negative_calories or 0
            except Exception as e:
                report.add_error("unit_check", f"Unit validation error: {e}")
            
        except Exception as e:
            report.add_error("validation", f"Error during validation: {e}")
        
        return report
    
    def _write_validation_report(self, metadata_dir: Path, report: ValidationReport):
        """Write validation report to file"""
        with open(metadata_dir / "validation_report.txt", 'w') as f:
            f.write(report.to_text())
    
    def _create_zip_file(self, export_dir: Path, zip_path: Path):
        """Create zip file from export directory"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in export_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(export_dir.parent)
                    zipf.write(file_path, arcname)

# Initialize worker on module import (commented out for now)
# export_worker.start()
