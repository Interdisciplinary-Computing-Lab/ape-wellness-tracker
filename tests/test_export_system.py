"""
Tests for the researcher-grade export system
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, date
from backend.models.export import (
    ExportAudit, ExportType, ExportFormat, ExportStatus, 
    ExportFilters, ValidationReport, ExportManifest
)
from backend.services.export_service import ExportService

class TestExportModels:
    """Test export models"""
    
    def test_export_filters_to_dict(self):
        """Test ExportFilters serialization"""
        filters = ExportFilters(
            date_from="2023-01-01",
            date_to="2023-12-31",
            ape_ids=[1, 2, 3],
            food_category_ids=[4, 5],
            include_calculated=True,
            include_identifiers=False
        )
        
        data = filters.to_dict()
        
        assert data['date_from'] == "2023-01-01"
        assert data['date_to'] == "2023-12-31"
        assert data['ape_ids'] == [1, 2, 3]
        assert data['food_category_ids'] == [4, 5]
        assert data['include_calculated'] is True
        assert data['include_identifiers'] is False
    
    def test_export_filters_from_dict(self):
        """Test ExportFilters deserialization"""
        data = {
            'date_from': '2023-01-01',
            'date_to': '2023-12-31',
            'ape_ids': [1, 2, 3],
            'food_category_ids': [4, 5],
            'include_calculated': True,
            'include_identifiers': False
        }
        
        filters = ExportFilters.from_dict(data)
        
        assert filters.date_from == "2023-01-01"
        assert filters.date_to == "2023-12-31"
        assert filters.ape_ids == [1, 2, 3]
        assert filters.food_category_ids == [4, 5]
        assert filters.include_calculated is True
        assert filters.include_identifiers is False
    
    def test_validation_report(self):
        """Test ValidationReport functionality"""
        report = ValidationReport()
        
        report.fk_integrity_errors = 5
        report.temporal_anomalies = 2
        report.duplicates = 1
        report.null_violations = {'Ape_Information.name': 1}
        report.unit_violations = 3
        report.add_error("test", "Test error message")
        
        text_report = report.to_text()
        
        assert "FK integrity: 5 errors" in text_report
        assert "Temporal anomalies: 2" in text_report
        assert "Duplicates: 1" in text_report
        assert "Unit violations: 3" in text_report
        assert "Ape_Information.name: 1" in text_report
        assert "Test error message" in text_report

class TestExportService:
    """Test export service functionality"""
    
    @patch('backend.services.export_service.db')
    def test_hash_identifier(self):
        """Test identifier hashing for privacy"""
        service = ExportService()
        
        # Test hashing
        identifier = "test_identifier"
        hashed = service._hash_identifier(identifier)
        
        assert len(hashed) == 16  # Should be truncated to 16 chars
        assert hashed != identifier  # Should be different from original
        assert hashed.isalnum()  # Should be alphanumeric
    
    def test_export_manifest(self):
        """Test export manifest generation"""
        filters = ExportFilters()
        table_counts = {'Ape_Information': 10, 'Meal_Logs': 100}
        table_checksums = {'Ape_Information': 'abc123', 'Meal_Logs': 'def456'}
        
        manifest = ExportManifest(
            export_type="raw",
            format="csv_pack",
            filters=filters,
            table_counts=table_counts,
            table_checksums=table_checksums
        )
        
        manifest_dict = manifest.to_dict()
        
        assert manifest_dict['type'] == "raw"
        assert manifest_dict['format'] == "csv_pack"
        assert manifest_dict['schema_version'] == "1.2"
        assert 'export_time_utc' in manifest_dict
        assert manifest_dict['tables']['Ape_Information']['rows'] == 10
        assert manifest_dict['tables']['Ape_Information']['sha256'] == 'abc123'

class TestExportAPI:
    """Test export API endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test app"""
        from run import app
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_create_export_request_validation(self, client):
        """Test export request validation"""
        # Test missing type
        response = client.post('/api/v1/exports', 
                             json={'format': 'csv_pack', 'filters': {}})
        assert response.status_code == 400
        assert 'type must be' in response.json['error']
        
        # Test invalid type
        response = client.post('/api/v1/exports', 
                             json={'type': 'invalid', 'format': 'csv_pack', 'filters': {}})
        assert response.status_code == 400
        
        # Test invalid format
        response = client.post('/api/v1/exports', 
                             json={'type': 'raw', 'format': 'invalid', 'filters': {}})
        assert response.status_code == 400
        
        # Test invalid date format
        response = client.post('/api/v1/exports', 
                             json={
                                 'type': 'raw', 
                                 'format': 'csv_pack', 
                                 'filters': {'date_from': 'invalid-date'}
                             })
        assert response.status_code == 400
    
    def test_schema_endpoint(self, client):
        """Test schema metadata endpoint"""
        response = client.get('/api/v1/metadata/schema')
        
        assert response.status_code == 200
        data = response.json
        
        assert 'schema_version' in data
        assert data['schema_version'] == "1.2"
        assert 'tables' in data
        
        # Check table structure
        table_names = [table['name'] for table in data['tables']]
        assert 'Ape_Information' in table_names
        assert 'Meal_Logs' in table_names
        assert 'Meal_Definitions' in table_names
        assert 'Food_Categories' in table_names

class TestDataValidation:
    """Test data validation functionality"""
    
    def test_fk_integrity_validation(self):
        """Test foreign key integrity validation"""
        # This would test actual FK validation logic
        # For now, just test the structure
        report = ValidationReport()
        
        # Simulate FK errors
        report.fk_integrity_errors = 2
        
        text = report.to_text()
        assert "FK integrity: 2 errors" in text
    
    def test_temporal_validation(self):
        """Test temporal data validation"""
        report = ValidationReport()
        
        # Simulate temporal anomalies
        report.temporal_anomalies = 1
        
        text = report.to_text()
        assert "Temporal anomalies: 1" in text

class TestPrivacyFeatures:
    """Test privacy and security features"""
    
    def test_identifier_hashing(self):
        """Test that identifiers are properly hashed"""
        service = ExportService()
        
        original_id = "researcher123"
        hashed_id = service._hash_identifier(original_id)
        
        # Should be different from original
        assert hashed_id != original_id
        
        # Should be consistent for same input
        hashed_id2 = service._hash_identifier(original_id)
        assert hashed_id == hashed_id2
        
        # Should be different for different inputs
        different_id = "researcher456"
        different_hashed = service._hash_identifier(different_id)
        assert hashed_id != different_hashed
    
    def test_privacy_settings(self):
        """Test privacy settings in export filters"""
        # Test with identifiers disabled
        filters = ExportFilters(include_identifiers=False)
        assert filters.include_identifiers is False
        
        # Test with identifiers enabled
        filters = ExportFilters(include_identifiers=True)
        assert filters.include_identifiers is True

# Integration tests would go here
class TestIntegration:
    """Integration tests for the export system"""
    
    @patch('backend.services.export_service.export_worker')
    def test_export_job_creation(self, mock_worker):
        """Test creating an export job"""
        # This would test the full flow of creating an export job
        # For now, just verify the structure
        service = ExportService()
        
        # Mock the database session
        with patch('backend.services.export_service.db.session') as mock_session:
            job_id = service.create_export_job(1, {
                'type': 'raw',
                'format': 'csv_pack',
                'filters': {}
            })
            
            assert job_id is not None
            assert len(job_id) == 36  # UUID length

if __name__ == '__main__':
    pytest.main([__file__])
