#!/bin/bash
# Package desktop application into a zip file for distribution

set -e

echo "📦 Packaging Desktop Application..."
echo ""

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build the application
echo "🔨 Building application..."
./build_mac.sh

# Check if build was successful
if [ -d "dist/Ape Wellness Tracker.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    
    # Create zip file
    echo "📦 Creating zip file..."
    cd dist
    zip -r "Ape Wellness Tracker-macOS.zip" "Ape Wellness Tracker.app" > /dev/null
    cd ..
    
    # Get file size
    ZIP_SIZE=$(du -h "dist/Ape Wellness Tracker-macOS.zip" | cut -f1)
    
    echo ""
    echo "✅ Package created successfully!"
    echo ""
    echo "📁 Location: $(pwd)/dist/Ape Wellness Tracker-macOS.zip"
    echo "📊 Size: $ZIP_SIZE"
    echo ""
    echo "The zip file contains the complete macOS application."
    echo "Users can extract it and run 'Ape Wellness Tracker.app'"
else
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi



