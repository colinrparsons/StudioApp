#!/bin/bash
# set -e (disabled for debugging)

# Set up directories
export PORTABLE_ROOT="$HOME/portable_magick"
export PATH="$PORTABLE_ROOT/im7/bin:$PORTABLE_ROOT/gs/bin:$PORTABLE_ROOT/gifsicle/bin:$PATH"
mkdir -p "$PORTABLE_ROOT"

# 1. Build Ghostscript (disabled for debugging)
# cd "$HOME"
# curl -LO https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10010/ghostscript-10.05.1.tar.gz
# tar xzf ghostscript-10.05.1.tar.gz
# cd ghostscript-10.05.1
# ./configure --prefix="$PORTABLE_ROOT/gs" --enable-dynamic --disable-hidden-visibility --disable-cups
# make -j$(sysctl -n hw.ncpu)
# make install
# cd ..
# rm -rf ghostscript-10.05.1 ghostscript-10.05.1.tar.gz

# 2. Build ImageMagick 6
curl -LO https://download.imagemagick.org/archive/releases/ImageMagick-7.1.1-21.tar.xz
tar xf ImageMagick-7.1.1-21.tar.xz

echo "=== BEGIN ZUTIL.H PATCH DIAGNOSTICS ==="
zutil_path="$(pwd)/ImageMagick-7.1.1-21/zlib/zutil.h"
if [ ! -f "$zutil_path" ]; then
  echo "zutil.h not found at $zutil_path. Attempting to download and extract zlib..."
  cd ImageMagick-7.1.1-21
  curl -L -o zlib-1.2.13.tar.gz https://zlib.net/zlib-1.2.13.tar.gz
  if ! tar xzf zlib-1.2.13.tar.gz; then
    echo "ERROR: Failed to extract zlib-1.2.13.tar.gz. The file may be corrupt or not a valid archive."
    file zlib-1.2.13.tar.gz
    exit 98
  fi
  mv zlib-1.2.13 zlib
  rm zlib-1.2.13.tar.gz
  cd ..
  if [ ! -f "$zutil_path" ]; then
    echo "ERROR: zutil.h still not found at $zutil_path after attempting to download zlib. Exiting build."
    exit 99
  fi
fi
ls -l "$zutil_path"
echo "--- zutil.h lines 1-20 before patch ---"
sed -n '1,20p' "$zutil_path"
echo "--- zutil.h lines 140-160 before patch ---"
sed -n '140,160p' "$zutil_path"
echo "--- end of pre-patch diagnostics ---"

# Aggressively comment out any fdopen macro definition in zutil.h (macOS fix)
sed -i.bak '/define[[:space:]]*fdopen.*NULL/s/^/\//\//g' "$zutil_path"

# Print the relevant lines for verification
echo '--- zutil.h lines 140-160 after patch ---'
sed -n '140,160p' "$zutil_path"
echo '=== END ZUTIL.H PATCH DIAGNOSTICS ==='

cd ImageMagick-7.1.1-21
./configure --prefix="$PORTABLE_ROOT/im6" \
  --with-gslib \
  --with-gs-font-dir="$PORTABLE_ROOT/gs/share/ghostscript/fonts" \
  --with-gs="$PORTABLE_ROOT/gs/bin/gs" \
  --without-lqr
make -j$(sysctl -n hw.ncpu)
make install
cd ..
rm -rf ImageMagick-7.1.1-21 ImageMagick-7.1.1-21.tar.gz

# 3. Build Gifsicle
curl -LO https://www.lcdf.org/gifsicle/gifsicle-1.94.tar.gz
tar xzf gifsicle-1.94.tar.gz
cd gifsicle-1.94
./configure --prefix="$PORTABLE_ROOT/gifsicle"
make -j$(sysctl -n hw.ncpu)
make install
cd ..
rm -rf gifsicle-1.94 gifsicle-1.94.tar.gz

# 4. Prepare for bundling
mkdir -p "$PORTABLE_ROOT/bundle/bin" "$PORTABLE_ROOT/bundle/lib"
cp "$PORTABLE_ROOT/im6/bin/"* "$PORTABLE_ROOT/bundle/bin/"
cp "$PORTABLE_ROOT/gs/bin/gs" "$PORTABLE_ROOT/bundle/bin/"
cp "$PORTABLE_ROOT/gifsicle/bin/gifsicle" "$PORTABLE_ROOT/bundle/bin/"

# 5. Copy non-system libraries (optional, see notes below)
# Use otool -L to check dependencies and copy any non-system libraries to bundle/lib
echo "Check dependencies with otool -L and copy any non-system libraries to $PORTABLE_ROOT/bundle/lib as needed."
echo "Done! Your portable binaries are in $PORTABLE_ROOT/bundle/bin"
