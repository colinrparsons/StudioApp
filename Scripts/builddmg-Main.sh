#!/bin/sh
# Create a folder (named dmg) to prepare our DMG in (if it doesn't already exist).
mkdir -p dist/dmg
# Empty the dmg folder.
rm -r dist/dmg/*
# Copy the app bundle to the dmg folder.
cp -r "dist/GDNPro.app" dist/dmg
# If the DMG already exists, delete it.
test -f "dist/GDNPro.dmg" && rm "dist/GDNPro.dmg"
create-dmg \
  --volname "GDNPro" \
  --volicon "GDNPro.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "GDNPro.app" 175 120 \
  --hide-extension "GDNPro.app" \
  --app-drop-link 425 120 \
  "dist/GDNPro.dmg" \
  "dist/dmg/"

