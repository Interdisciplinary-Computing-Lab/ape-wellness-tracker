#!/bin/bash
# Create a DMG installer for macOS
# This script creates a professional DMG file for distribution

set -e  # Exit on error

echo "Creating DMG installer for macOS..."
echo ""

# Check if app bundle exists
if [ ! -d "dist/Ape_Meal_Tracker.app" ]; then
    echo "Error: App bundle not found at dist/Ape_Meal_Tracker.app"
    echo "Please run build_mac.sh first to create the app bundle."
    exit 1
fi

# Clean up any existing DMG
if [ -f "dist/Ape_Meal_Tracker.dmg" ]; then
    echo "Removing existing DMG..."
    rm -f "dist/Ape_Meal_Tracker.dmg"
fi

# Create a temporary directory for DMG contents
DMG_TEMP="dist/dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copy app bundle to temp directory
echo "Copying app bundle..."
cp -R "dist/Ape_Meal_Tracker.app" "$DMG_TEMP/"

# Create Applications symlink (standard Mac DMG convention)
echo "Creating Applications symlink..."
ln -s /Applications "$DMG_TEMP/Applications"

# Create a README file
echo "Creating README..."
cat > "$DMG_TEMP/README.txt" << 'EOF'
APE MEAL TRACKER - INSTALLATION INSTRUCTIONS
============================================

1. Drag "Ape Meal Tracker.app" to the Applications folder
2. Open Applications and double-click "Ape Meal Tracker"
3. On first launch, macOS may show a security warning:
   - Go to System Preferences > Security & Privacy
   - Click "Open Anyway" next to the warning message
   - Or right-click the app and select "Open"

SYSTEM REQUIREMENTS:
- macOS 10.13 (High Sierra) or later
- 200MB free disk space
- No internet connection required

SUPPORT:
For technical support, contact:
dylandaner@me.com
zmielko@highlands.edu

Copyright © 2024 Ape Initiative
EOF

# Create the DMG
echo "Creating DMG file..."
DMG_NAME="Ape_Meal_Tracker"
VOLUME_NAME="Ape Meal Tracker"

hdiutil create -volname "$VOLUME_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov \
    -format UDZO \
    -imagekey zlib-level=9 \
    "dist/${DMG_NAME}.dmg"

# Clean up temp directory
echo "Cleaning up..."
rm -rf "$DMG_TEMP"

# Verify DMG was created
if [ -f "dist/${DMG_NAME}.dmg" ]; then
    echo ""
    echo "DMG created successfully!"
    echo ""
    echo "DMG file location: dist/${DMG_NAME}.dmg"
    echo ""
    echo "To test the DMG, run:"
    echo "  open 'dist/${DMG_NAME}.dmg'"
    echo ""
    
    # Optional: Code sign the DMG
    if [ -n "$APPLE_DEVELOPER_ID" ]; then
        echo "Signing DMG with Developer ID..."
        codesign --force --verify --verbose --sign "$APPLE_DEVELOPER_ID" "dist/${DMG_NAME}.dmg"
        if [ $? -eq 0 ]; then
            echo "DMG signing successful!"
        else
            echo "Warning: DMG signing failed, but DMG is still usable"
        fi
    fi
else
    echo "DMG creation failed."
    exit 1
fi

