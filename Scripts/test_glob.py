import glob
import os

files = [
    f for f in glob.glob('portable_magick/**/*', recursive=True)
    if os.path.isfile(f)
]
print(files)
