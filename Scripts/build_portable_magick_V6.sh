#!/bin/bash
set -e

# Set up directories
export PORTABLE_ROOT="$HOME/portable_magick"
export PATH="$PORTABLE_ROOT/im6/bin:$PORTABLE_ROOT/gs/bin:$PORTABLE_ROOT/gifsicle/bin:$PATH"
mkdir -p "$PORTABLE_ROOT"

# 1. Build Ghostscript
cd "$HOME"
curl -LO https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs10051/ghostscript-10.05.1.tar.gz
tar xzf ghostscript-10.05.1.tar.gz
cd ghostscript-10.05.1
./configure --prefix="$PORTABLE_ROOT/gs" --enable-dynamic --disable-hidden-visibility --disable-cups
make -j$(sysctl -n hw.ncpu)
make install
cd ..
rm -rf ghostscript-10.05.1 ghostscript-10.05.1.tar.gz

# 2. Build ImageMagick 6
curl -LO https://download.imagemagick.org/archive/releases/mageMagick-6.9.13-0.tar.xz
tar xf ImageMagick-6.9.13-0.tar.xz
cd ImageMagick-6.9.13-0
./configure --prefix="$PORTABLE_ROOT/im6" \
  --with-gslib \
  --with-gs-font-dir="$PORTABLE_ROOT/gs/share/ghostscript/fonts" \
  --with-gs="$PORTABLE_ROOT/gs/bin/gs" \
  --without-lqr
make -j$(sysctl -n hw.ncpu)
make install
cd ..
rm -rf mageMagick-6.9.13-0 mageMagick-6.9.13-0.tar.gz

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
