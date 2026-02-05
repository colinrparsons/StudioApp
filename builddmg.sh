#!/bin/sh
# Full build, permission fix, and DMG packaging script for GDNPro

# Set paths
DMG_FOLDER="dist/dmg"
DMG_NAME="dist/Image Converter.dmg"
APP_NAME="Image Converter.app"
ICON_NAME="DImageConverter.icns"
BACKGROUND_IMAGE="background.png"
READ_ME="README.md"


# 3. Prepare the DMG folder
mkdir -p "$DMG_FOLDER"
rm -rf "$DMG_FOLDER"/*

# 4. Copy the app bundle and ReadMe PDF to the dmg folder
cp -r "dist/$APP_NAME" "$DMG_FOLDER"
cp "$READ_ME" "$DMG_FOLDER"

# 5. If the DMG already exists, delete it
test -f "$DMG_NAME" && rm "$DMG_NAME"

# 6. Use create-dmg to build the DMG with the background image and PDF
create-dmg \
  --volname "Image Converter" \
  --volicon "$ICON_NAME" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "$APP_NAME" 100 120 \
  --icon "README.md" 280 120 \
  --hide-extension "$APP_NAME" \
  --app-drop-link 470 120 \
  --background "$BACKGROUND_IMAGE" \
  "$DMG_NAME" \
  "$DMG_FOLDER/"
