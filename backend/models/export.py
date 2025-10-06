"""
Export system models for researcher-grade data exports
"""

from backend.extensions import db
from datetime import datetime
import json
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class ExportType(Enum):
    RAW = "raw"
    DERIVED = "derived"

class ExportFormat(Enum):
    CSV_PACK = "csv_pack"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    JSONL_PACK = "jsonl_pack"

class ExportStatus(Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ExportAudit(db.Model):
    """
    Audit trail for export requests
    """
    __tablename__ = 'export_audit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type = db.Column(db.String(20), nullable=False)
    format = db.Column(db.String(20), nullable=False)
    filters_json = db.Column(db.Text, nullable=False)
    row_counts_json = db.Column(db.Text, nullable=True)
    download_ip = db.Column(db.String(45), nullable=True)
    job_id = db.Column(db.String(36), unique=True, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    download_url = db.Column(db.Text, nullable=True)
    progress = db.Column(db.Integer, default=0, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='exports')
    
    @property
    def filters(self) -> Dict[str, Any]:
        """Parse filters JSON"""
        return json.loads(self.filters_json) if self.filters_json else {}
    
    @filters.setter
    def filters(self, value: Dict[str, Any]):
        """Set filters JSON"""
        self.filters_json = json.dumps(value)
    
    @property
    def row_counts(self) -> Dict[str, int]:
        """Parse row counts JSON"""
        return json.loads(self.row_counts_json) if self.row_counts_json else {}
    
    @row_counts.setter
    def row_counts(self, value: Dict[str, int]):
        """Set row counts JSON"""
        self.row_counts_json = json.dumps(value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'download_url': self.download_url,
            'progress': self.progress,
            'error': self.error_message
        }

@dataclass
class ExportFilters:
    """Export filter configuration"""
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    ape_ids: Optional[List[int]] = None
    food_category_ids: Optional[List[int]] = None
    include_calculated: bool = False
    include_identifiers: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'ape_ids': self.ape_ids or [],
            'food_category_ids': self.food_category_ids or [],
            'include_calculated': self.include_calculated,
            'include_identifiers': self.include_identifiers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportFilters':
        """Create from dictionary"""
        return cls(
            date_from=data.get('date_from'),
            date_to=data.get('date_to'),
            ape_ids=data.get('ape_ids'),
            food_category_ids=data.get('food_category_ids'),
            include_calculated=data.get('include_calculated', False),
            include_identifiers=data.get('include_identifiers', False)
        )

@dataclass
class ExportRequest:
    """Export request configuration"""
    type: ExportType
    format: ExportFormat
    filters: ExportFilters
    user_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        return {
            'type': self.type.value,
            'format': self.format.value,
            'filters': self.filters.to_dict()
        }

class ValidationReport:
    """Data validation report"""
    
    def __init__(self):
        self.fk_integrity_errors = 0
        self.temporal_anomalies = 0
        self.duplicates = 0
        self.null_violations = {}
        self.unit_violations = 0
        self.row_count_mismatches = {}
        self.file_checksum_errors = 0
        self.errors = []
    
    def add_error(self, category: str, message: str):
        """Add validation error"""
        self.errors.append(f"{category}: {message}")
    
    def to_text(self) -> str:
        """Generate validation report text"""
        report = []
        report.append("VALIDATION REPORT")
        report.append("=" * 50)
        report.append(f"FK integrity: {'OK' if self.fk_integrity_errors == 0 else f'{self.fk_integrity_errors} errors'}")
        report.append(f"Temporal anomalies: {self.temporal_anomalies}")
        report.append(f"Duplicates: {self.duplicates}")
        report.append(f"Unit violations: {self.unit_violations}")
        report.append(f"File checksum errors: {self.file_checksum_errors}")
        
        if self.null_violations:
            report.append("Null violations:")
            for table, count in self.null_violations.items():
                report.append(f"  {table}: {count}")
        
        if self.row_count_mismatches:
            report.append("Row count mismatches:")
            for table, mismatch in self.row_count_mismatches.items():
                report.append(f"  {table}: {mismatch}")
        
        if self.errors:
            report.append("\nDetailed errors:")
            for error in self.errors:
                report.append(f"  - {error}")
        
        return "\n".join(report)

class ExportManifest:
    """Export manifest data structure"""
    
    def __init__(self, export_type: str, format: str, filters: ExportFilters, 
                 table_counts: Dict[str, int], table_checksums: Dict[str, str]):
        self.export_time_utc = datetime.utcnow().isoformat() + 'Z'
        self.type = export_type
        self.format = format
        self.schema_version = "1.2"
        self.app_version = "3.0.5"  # Update as needed
        self.filters = filters.to_dict()
        self.privacy = {
            'include_identifiers': filters.include_identifiers,
            'researcher_id_scheme': 'hash:sha256(salt+user_id)' if not filters.include_identifiers else 'plain'
        }
        self.tables = {
            table: {
                'rows': count,
                'sha256': checksums.get(table, '')
            }
            for table, count in table_counts.items()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'export_time_utc': self.export_time_utc,
            'type': self.type,
            'format': self.format,
            'schema_version': self.schema_version,
            'app_version': self.app_version,
            'filters': self.filters,
            'privacy': self.privacy,
            'tables': self.tables
        }
