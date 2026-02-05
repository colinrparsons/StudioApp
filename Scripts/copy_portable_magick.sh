#!/bin/bash
set -e

# Source and destination directories
SRC_ROOT="$HOME/portable_magick/bundle"
DEST_ROOT="$HOME/Desktop/GDNPro/portable_magick"

# Create destination directory if it doesn't exist
mkdir -p "$DEST_ROOT"

# Copy bin directory
if [ -d "$SRC_ROOT/bin" ]; then
    rm -rf "$DEST_ROOT/bin"
    cp -R "$SRC_ROOT/bin" "$DEST_ROOT/"
    echo "Copied bin directory."
else
    echo "No bin directory found in $SRC_ROOT."
fi

# Copy lib directory if it exists
if [ -d "$SRC_ROOT/lib" ]; then
    rm -rf "$DEST_ROOT/lib"
    cp -R "$SRC_ROOT/lib" "$DEST_ROOT/"
    echo "Copied lib directory."
else
    echo "No lib directory found in $SRC_ROOT. (This is OK if your build does not use shared libraries)"
fi

echo "Portable ImageMagick, Ghostscript, and Gifsicle binaries are now in $DEST_ROOT."
