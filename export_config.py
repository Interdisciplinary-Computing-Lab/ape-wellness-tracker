"""
Configuration for the export system
"""

import os

class ExportConfig:
    """Export system configuration"""
    
    # Export temporary directory
    TEMP_DIR = os.getenv("EXPORT_TEMP_DIR", "/tmp/exports")
    
    # Signed URL time-to-live in seconds
    SIGNED_URL_TTL = int(os.getenv("EXPORT_SIGNED_URL_TTL", "3600"))
    
    # Salt for hashing identifiers
    HASH_SALT = os.getenv("EXPORT_HASH_SALT", "default_salt_change_in_production")
    
    # Maximum file size for exports (in bytes)
    MAX_FILE_SIZE = int(os.getenv("EXPORT_MAX_FILE_SIZE", "1000000000"))  # 1GB
    
    # Export timeout in seconds
    EXPORT_TIMEOUT = int(os.getenv("EXPORT_TIMEOUT", "3600"))  # 1 hour
    
    # Number of worker threads for export processing
    WORKER_THREADS = int(os.getenv("EXPORT_WORKER_THREADS", "2"))
    
    # Enable debug mode for exports
    DEBUG = os.getenv("EXPORT_DEBUG", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        errors = []
        
        # Check if temp directory is writable
        if not os.access(cls.TEMP_DIR, os.W_OK):
            errors.append(f"Export temp directory is not writable: {cls.TEMP_DIR}")
        
        # Check salt length
        if len(cls.HASH_SALT) < 16:
            errors.append("Export hash salt should be at least 16 characters long")
        
        # Check TTL values
        if cls.SIGNED_URL_TTL < 60:
            errors.append("Signed URL TTL should be at least 60 seconds")
        
        if cls.EXPORT_TIMEOUT < 60:
            errors.append("Export timeout should be at least 60 seconds")
        
        if errors:
            raise ValueError("Export configuration errors: " + "; ".join(errors))
        
        return True
