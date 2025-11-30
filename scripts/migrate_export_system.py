#!/usr/bin/env python3
"""
Migration script to add export system tables
"""

from run import app
from backend.extensions import db
from sqlalchemy import text

def migrate_export_system():
    """Add export system tables"""
    with app.app_context():
        try:
            # Create schema_version table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    id INTEGER PRIMARY KEY,
                    version TEXT NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create export_audit table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS export_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    type TEXT NOT NULL CHECK (type IN ('raw', 'derived')),
                    format TEXT NOT NULL CHECK (format IN ('csv_pack', 'parquet', 'sqlite', 'jsonl_pack')),
                    filters_json TEXT NOT NULL,
                    row_counts_json TEXT,
                    download_ip TEXT,
                    job_id TEXT UNIQUE,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed')),
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP,
                    error_message TEXT,
                    download_url TEXT,
                    FOREIGN KEY (user_id) REFERENCES user (id)
                )
            """))
            
            # Insert schema version
            db.session.execute(text("""
                INSERT OR IGNORE INTO schema_version (version) VALUES ('1.2')
            """))
            
            db.session.commit()
            print("Export system tables created successfully!")
            return True
            
        except Exception as e:
            print(f"Error creating export system tables: {e}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    migrate_export_system()
