#!/bin/bash
# Make all binaries in portable_magick/bin executable after PyInstaller build

TARGET_DIR="dist/GDNPro/_internal/portable_magick/bin"

if [ -d "$TARGET_DIR" ]; then
    echo "Setting executable permissions on $TARGET_DIR/*"
    chmod -R +x "$TARGET_DIR"
else
    echo "Directory $TARGET_DIR not found!"
fi