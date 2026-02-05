import os
from setuptools import setup, find_packages

APP = ['app.py']

# Helper to recursively collect all files in portable_magick as package data

# --- Ensure all files in portable_magick are included for both Python and py2app ---
def package_files(directory):
    """
    Recursively collect all files in 'directory' for package_data.
    Returns paths relative to the package root.
    """
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            full_path = os.path.join(path, filename)
            rel_path = os.path.relpath(full_path, '.')  # relative to project root
            paths.append(rel_path)
    return paths

# Only keep data_files for icons/config for py2app, not portable_magick
DATA_FILES = [
    ('icons', ['icons/add.png', 'icons/delete.png', 'icons/pdf.png', 'icons/film.png', 'icons/gif.png']),
    ('config', ['config/database.db']),
]

OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'GDNPro.icns',
    # List the full portable_magick directory to ensure all subfolders and files are included
    'resources': ['portable_magick', 'icons', 'config'],
    # Add any other py2app options here
}

setup(
    app=APP,
    packages=find_packages(),
    # This ensures all files in portable_magick (and subfolders) are included in the package
    package_data={
        '': package_files('portable_magick'),
    },
    include_package_data=True,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='GDNPro',
)

# --- After building, check that all files from portable_magick are present in the .app bundle ---
# You can run this snippet manually after build to verify:
# import filecmp, os
# src = set(os.path.relpath(os.path.join(dp, f), 'portable_magick') for dp, dn, fn in os.walk('portable_magick') for f in fn)
# dst = set(os.path.relpath(os.path.join(dp, f), 'dist/GDNPro.app/Contents/Resources/portable_magick') for dp, dn, fn in os.walk('dist/GDNPro.app/Contents/Resources/portable_magick') for f in fn)
# missing = src - dst
# if missing:
#     print('Missing from bundle:', missing)
# else:
#     print('All portable_magick files bundled!')

