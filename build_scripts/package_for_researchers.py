#!/usr/bin/env python3
"""
Package the desktop application for distribution to researchers.

This script creates a zip file containing:
- The executable
- Researcher instructions
- README file

Usage:
    python package_for_researchers.py
"""

import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

def create_distribution_package():
    """Create a zip file for researcher distribution"""
    
    dist_folder = Path('distribution')
    
    if not dist_folder.exists():
        print("ERROR: 'distribution' folder not found!")
        print("Please run 'python build_desktop.py' first to build the executable.")
        return False
    
    # Check if executable exists
    exe_files = list(dist_folder.glob('ApeWellnessTracker*'))
    if not exe_files:
        print("ERROR: No executable found in 'distribution' folder!")
        print("Please run 'python build_desktop.py' first to build the executable.")
        return False
    
    # Create zip filename with date
    date_str = datetime.now().strftime("%Y%m%d")
    zip_filename = f"ApeWellnessTracker-Desktop-v1.0-{date_str}.zip"
    
    print(f"Creating distribution package: {zip_filename}")
    print("=" * 60)
    
    # Create zip file
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add all files from distribution folder
        for file_path in dist_folder.rglob('*'):
            if file_path.is_file():
                # Get relative path for zip
                arcname = file_path.relative_to(dist_folder)
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")
    
    # Get file size
    file_size_mb = os.path.getsize(zip_filename) / (1024 * 1024)
    
    print("=" * 60)
    print(f"Package created successfully!")
    print(f"\nFile: {zip_filename}")
    print(f"Size: {file_size_mb:.1f} MB")
    print(f"\nThis package is ready to send to researchers.")
    print(f"\nContents:")
    print(f"  - Executable: ApeWellnessTracker.exe")
    print(f"  - Instructions: RESEARCHER_INSTRUCTIONS.txt")
    print(f"  - README: DESKTOP_README.md (if present)")
    
    return True

def main():
    """Main function"""
    print("Ape Wellness Tracker - Researcher Distribution Package")
    print("=" * 60)
    print()
    
    if create_distribution_package():
        print("\nReady to distribute!")
        print("\nNext steps:")
        print("  1. Test the zip file by extracting it")
        print("  2. Verify the executable runs correctly")
        print("  3. Send the zip file to researchers")
    else:
        print("\nPackage creation failed.")
        print("Please ensure you've built the executable first:")
        print("  python build_desktop.py")

if __name__ == '__main__':
    main()

