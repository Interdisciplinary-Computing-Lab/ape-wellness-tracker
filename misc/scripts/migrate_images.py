#!/usr/bin/env python3
"""
Database migration script to add BLOB image storage to the Apes table.
This script will:
1. Add new columns for image_data and image_mime_type
2. Migrate existing image filenames to the new system (if files exist)
3. Update the database schema
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend import create_app
from backend.extensions import db
from backend.models.entry import Apes
from sqlalchemy import text

def migrate_database():
    """Migrate the database to include BLOB image storage"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting database migration for image BLOB storage...")
        
        # Check if columns already exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('apes')]
        
        if 'image_data' in columns and 'image_mime_type' in columns:
            print("✅ BLOB columns already exist. Migration not needed.")
            return
        
        # Add new columns
        print("📝 Adding new BLOB columns to apes table...")
        try:
            # Add image_data column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE apes 
                    ADD COLUMN image_data BLOB
                """))
                conn.commit()
            print("✅ Added image_data column")
            
            # Add image_mime_type column
            with db.engine.connect() as conn:
                conn.execute(text("""
                    ALTER TABLE apes 
                    ADD COLUMN image_mime_type VARCHAR(100)
                """))
                conn.commit()
            print("✅ Added image_mime_type column")
            
        except Exception as e:
            print(f"❌ Error adding columns: {e}")
            return
        
        # Try to migrate existing image files to BLOB storage
        print("🖼️  Attempting to migrate existing image files...")
        apes = Apes.query.all()
        migrated_count = 0
        
        for ape in apes:
            if ape.image_filename:
                image_path = project_root / 'backend' / 'static' / 'images' / ape.image_filename
                
                if image_path.exists():
                    try:
                        # Read the image file
                        with open(image_path, 'rb') as f:
                            image_data = f.read()
                        
                        # Determine MIME type based on file extension
                        ext = image_path.suffix.lower()
                        mime_types = {
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.png': 'image/png',
                            '.gif': 'image/gif',
                            '.webp': 'image/webp'
                        }
                        mime_type = mime_types.get(ext, 'image/jpeg')
                        
                        # Update the ape record
                        ape.image_data = image_data
                        ape.image_mime_type = mime_type
                        
                        migrated_count += 1
                        print(f"✅ Migrated image for {ape.ape_name}: {ape.image_filename}")
                        
                    except Exception as e:
                        print(f"⚠️  Could not migrate image for {ape.ape_name}: {e}")
                else:
                    print(f"⚠️  Image file not found for {ape.ape_name}: {ape.image_filename}")
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"✅ Successfully migrated {migrated_count} images to BLOB storage")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()
            return
        
        print("🎉 Database migration completed successfully!")
        print("\n📋 Summary:")
        print(f"   - Added image_data (BLOB) column")
        print(f"   - Added image_mime_type (VARCHAR) column")
        print(f"   - Migrated {migrated_count} existing images to BLOB storage")
        print("\n💡 The application now supports:")
        print("   - Direct image uploads during ape creation")
        print("   - Image uploads/removal from ape profile pages")
        print("   - Secure BLOB storage in the database")
        print("   - Automatic fallback to static files for backward compatibility")

if __name__ == '__main__':
    migrate_database() 