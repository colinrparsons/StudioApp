# -*- mode: python ; coding: utf-8 -*-

import glob
import os

block_cipher = None

# Recursively add all files from portable_magick

def collect_data_files(src_folder, dst_folder):
    import os
    import glob
    data_files = []
    for f in glob.glob(os.path.join(src_folder, '**', '*'), recursive=True):
        if os.path.isfile(f):
            rel_dir = os.path.relpath(os.path.dirname(f), src_folder)
            target_dir = os.path.join(dst_folder, rel_dir) if rel_dir != '.' else dst_folder
            data_files.append((os.path.abspath(f), target_dir))
    return data_files

portable_magick_datas = collect_data_files('portable_magick', 'portable_magick')
licenses_datas = collect_data_files('licenses', 'licenses')


project_dir = os.path.abspath('.')
a = Analysis(
    ['app.py'],
    # Always resolve relative to this spec file's directory
    pathex=[project_dir],
    binaries=[],
    # Always include all files from portable_magick directory
    # This ensures the binaries are included in the bundle
    # If you want to debug what is being added, uncomment the print below
    # print('Including portable_magick files:', portable_magick_datas)
    datas=[
        ('icons/add.png', 'icons'),
        ('config/database.db', 'config'),
        ('icons/delete.png', 'icons'),
        ('icons/pdf.png', 'icons'),
        ('icons/film.png', 'icons'),
        ('icons/gif.png', 'icons'),
    ] + portable_magick_datas + licenses_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Post-build: fix library references to prevent harfbuzz conflicts
# This ensures magick binary uses the correct harfbuzz library

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Image Converter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ImageConverter.icns',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Image Converter',
)
app = BUNDLE(
    coll,
    name='Image Converter.app',
    icon='ImageConverter.icns',
    bundle_identifier='com.yourcompany.ImageConverter',  # Set your bundle identifier here if desired
)

# Post-build: Fix library paths for harfbuzz
import subprocess
import shutil
app_path = os.path.join('dist', 'Image Converter.app')
if os.path.exists(app_path):
    frameworks_path = os.path.join(app_path, 'Contents', 'Frameworks')
    
    # Copy Homebrew's harfbuzz (with CoreText support) to portable_magick/lib
    # where the magick binary expects to find it via @rpath
    harfbuzz_dest = os.path.join(frameworks_path, 'portable_magick', 'lib', 'libharfbuzz.0.dylib')
    harfbuzz_homebrew = '/opt/homebrew/lib/libharfbuzz.0.dylib'
    
    if os.path.exists(harfbuzz_homebrew):
        # Ensure the lib directory exists
        os.makedirs(os.path.dirname(harfbuzz_dest), exist_ok=True)
        # Copy Homebrew's harfbuzz (has CoreText support that ImageMagick needs)
        shutil.copy2(harfbuzz_homebrew, harfbuzz_dest)
        print(f"Fixed harfbuzz: copied from {harfbuzz_homebrew} to {harfbuzz_dest}")
