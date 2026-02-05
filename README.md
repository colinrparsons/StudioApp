w# Image Converter

A fast, portable desktop app (PyQt5) for converting and size-targeting images, batch renaming files, and generating QR codes. Uses a bundled ImageMagick (`portable_magick`) for image processing. Supports converting PDF/JPG/PNG/GIF to JPG/PNG/GIF, with optional PDF trimming, drag-and-drop, folder processing, progress tracking, and configurable concurrency.

## Highlights
- Portable: ships with a private ImageMagick (`portable_magick`); no external installs.
- Multi-tab interface: Image Converter, File Renamer, and QR Code Generator.
- Multi-format: input = PDF, JPG/JPEG, PNG, GIF; output = JPG, PNG, GIF.
- Target size in KB with tolerance, using iterative quality/palette + resize/DPI strategy.
- Default mode (no target): PDF density 288 + 25% resize for all inputs.
- Trim PDFs option leverages TrimBox and geometric trim.
- Batch friendly: drag-and-drop and folder select.
- Parallel processing: configurable Workers (1–16, default = min(5, CPU cores)).
- File renaming with regex patterns, case conversion, and image orientation detection.
- QR Code generation from Excel data with multiple output formats (PNG, SVG, TIFF, EPS, PDF).
- Outputs saved next to source files.

## Requirements
- macOS (tested). Python 3 with:
  - PyQt5
  - pandas (used by app, not performance-critical)
  - qrcode[pil] (for QR code generation)
  - openpyxl (for Excel file handling)
- The repository includes a `portable_magick` directory containing `bin/convert` and required libs.

## Install & Run
1. Create venv (recommended) and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   If there is no `requirements.txt`, install: `PyQt5`, `pandas`, `qrcode[pil]`, and `openpyxl`.

2. Launch the app:
   ```bash
   python app.py
   ```

The app will ensure `portable_magick/bin/convert` is executable and add the appropriate environment variables to call it.

## UI Overview

The application has three tabs:

### 1. Image Tab (Image Converter)
- Top bar
  - Select Folder: choose a directory to ingest files (PDF/JPG/PNG/GIF); spaces in filenames are replaced with `-`.
  - Clear List: clears the file list.
  - Progress: shows progress for current batch.
  - Workers: how many files to process in parallel (max workers for the thread pool). Default `min(5, CPU cores)`.
- Conversion controls
  - Output: choose `JPG`, `PNG`, or `GIF`.
  - Target KB: target size per file in kilobytes. Leave blank to use default behavior.
  - Tol %: tolerance window allowed around the target size (e.g., 10%).
  - Trim PDFs: if checked and input is PDF, use PDF trim logic.
- File list: shows input files added via drag-and-drop or folder selection and displays converted file size results.
- Process Files: runs the conversion on all files in the list.

### 2. Rename Tab (File Renamer)
Batch rename files with pattern matching and character replacement.
- Drag and drop files or select a folder to load files.
- Enable Illegal Chars and Patterns: removes illegal characters and applies regex patterns.
- Add Button: opens pattern manager to add/remove/reset regex patterns.
- Replace/With: simple character replacement (e.g., replace spaces with underscores).
- Case Conversion: Default, Capitals, Title, Lowercase.
- **Add Orientation (L/P/S)**: detect image dimensions and append L (Landscape), P (Portrait), or S (Square) as prefix or suffix.
- Export to .txt: export the rename list to a text file.
- Process: apply all renaming operations.

Default regex patterns include:
- `_x_` → `x`, `_X_` → `x`, `_~` → `~`, `~_` → `~`
- `_px` → `px`, `_-_` → `_`, ` - ` → `_`, ` ` → `_`
- `--_` → `_`, `_--` → `_`, `%` → `pct`
- `__+` → `_`, `--+` → `-`, `_mm` → `mm`

### 3. QR Code Tab (QR Code Generator)
Generate QR codes from Excel data or single entries.

**Excel Template Management:**
- Import Excel: load an Excel file with `name` and `url` columns.
- Export Template: create a dummy Excel template with example data.
- Export Data: export current data back to Excel.

**Single QR Code:**
- Name/Filename: output filename (without extension).
- URL: the data to encode in the QR code.
- Add to List: add entry to the batch list.

**QR Code Settings:**
- Output Format: PNG, SVG, TIFF, EPS, PDF.
- Size: QR code size in boxes (1-40, default 10).
- Border: border size in boxes (0-10, default 4).
- Error Correction: Low (L), Medium (M), Quartile (Q), High (H).
- Fill Color: foreground color (default black).
- Background Color: background color (default white).
- Output Directory: where to save generated QR codes.

**Actions:**
- Generate Single: create one QR code.
- Generate Batch (All): process all entries in the list.
- Clear List: remove all entries.

## Supported Workflows

### Image Converter
- Drag-and-Drop: drop files (.pdf/.jpg/.jpeg/.png/.gif) onto the window to add them.
- Select Folder: scans the chosen directory for supported file types and adds them to the list.
- Process Files: converts all files concurrently (up to `Workers`).

### File Renamer
- Drag-and-Drop: drop files or folders to add them to the rename list.
- Select Folder: recursively loads all files from a directory.
- Pattern Management: click "Add" to customize regex patterns for filename cleanup.
- Preview: see original → new filename before processing.
- Export: save the rename list to a text file for reference.

### QR Code Generator
- Excel Import: prepare a spreadsheet with columns `name` and `url`, then import.
- Single Entry: manually enter name and URL for one-off QR codes.
- Batch Processing: generate all QR codes from the loaded list at once.
- Color Customization: pick custom colors for QR code appearance.

## Project Structure

```
StudioApp/
├── app.py              # Main PyQt5 application and logic
├── renamer.py          # RenamerTab and PatternsDialog classes
├── qr_code.py          # QRCodeTab class for QR code generation
├── portable_magick/    # Bundled ImageMagick binaries and libraries
├── config/
│   └── database.db     # SQLite database for settings and patterns
├── icons/              # UI icons
└── README.md           # This file
```

## Conversion Logic (Image Tab)
The app executes ImageMagick `convert` with a portable environment.

- Output Location: converted files are written next to the originals in the same folder.
- Default Mode (no Target KB):
  - If input is PDF: set `-density 288` before reading.
  - For all inputs: apply `-resize 25%`.
  - Optionally apply Trim PDFs (see below).
- Targeted Mode (Target KB set):
  - JPG: binary search over `-quality` (range ~20–90). Always `-strip`, `-interlace Plane`, `-sampling-factor 4:2:0`.
  - PNG/GIF: binary search over `-colors` (palette size; range 256→16) with `-dither None`. PNG uses `-define png:compression-level=9`; GIF uses `-layers Optimize +map`.
  - Fallback when still too large: progressively `-resize` (100→90→80→70→60%).
  - For PDFs: also try a `-density` ladder (200→150→120→100) before the input.
  - The best attempt within ±Tol % is accepted; if none exactly match, the closest size is saved.

### Tolerance (Tol %)
Tolerance defines how tightly the output size must match the Target KB. The converter accepts the first result whose size falls within the window:

- Lower bound = `TargetKB × (1 - Tol/100)`
- Upper bound = `TargetKB × (1 + Tol/100)`

Examples (Target = 200 KB):

- Tol 5% → acceptable range is 190–210 KB
- Tol 10% → acceptable range is 180–220 KB
- Tol 15% → acceptable range is 170–230 KB

How it's used:

- During the search, each candidate conversion is measured; if it falls inside the range, it's accepted immediately.
- If no candidate lands inside the range after trying quality/palette and resize/density ladders, the closest attempt to Target is chosen and saved.

Recommendations:

- Start with 10% for a good balance of speed and precision.
- Use 5% if you need tighter control, but expect more iterations and occasional misses requiring downscaling.
- Use 15% for faster results when content compressibility varies a lot (e.g., screenshots vs. photos).

#### Quick Reference Table

Target KB vs acceptable ranges per tolerance:

| Target KB | Tol 5% (min–max KB) | Tol 10% (min–max KB) | Tol 15% (min–max KB) |
|-----------|----------------------|-----------------------|-----------------------|
| 100       | 95–105               | 90–110                | 85–115                |
| 150       | 142.5–157.5          | 135–165               | 127.5–172.5           |
| 200       | 190–210              | 180–220               | 170–230               |
| 300       | 285–315              | 270–330               | 255–345               |
| 500       | 475–525              | 450–550               | 425–575               |

Note: Ranges are illustrative; the app uses exact math: `TargetKB × (1 ± Tol/100)`.

### Trim PDFs
When Trim PDFs is enabled and the source is a PDF, the app adds:
- `-define pdf:use-trimbox=true` before reading the input to honor the PDF TrimBox.
- `-trim +repage` after reading to remove uniform borders.

Notes:
- If your PDFs use `CropBox`/`ArtBox` instead, this define can be changed to `pdf:use-cropbox=true` or `pdf:use-artbox=true` in code.
- `-trim` trims uniform color margins; irregular content edges are preserved.

## Concurrency (Workers)
- The app processes files in parallel using a thread pool: `max_workers = Workers`.
- Each task calls `convert` via subprocess, so work happens outside Python's GIL.
- Suggestions:
  - Many cores or smaller images: increase Workers.
  - Very large PDFs or limited RAM: reduce Workers to avoid contention.

## Settings Persistence
The app uses an SQLite database (`config/database.db`) to persist settings:
- Image tab: output format, resolution, tolerance, workers, timeout, trim PDFs, target KB.
- Rename tab: enable illegal chars, replace/with characters, case setting, **orientation detection**, custom patterns.
- QR Code tab: output format, size, border, error correction, colors, output directory.

## Error Handling & Logging
- The app prints debug information about the portable path configuration on startup.
- Conversion errors per file are logged to stdout; the app continues with remaining files.

## Tips
- Image Tab: Start with Target KB blank to sanity-check output (default 25% scale, 288 DPI for PDFs).
- Image Tab: Then set a realistic target and tolerance. Tight targets with high resolution may not be achievable without heavy downscaling.
- Rename Tab: Use the pattern manager to customize filename cleanup rules.
- QR Code Tab: Use Excel import for bulk QR code generation. The template export helps you format the data correctly.

## FAQ
- Q: Why are outputs not exactly at the target size?
  - A: We search within a tolerance (e.g., ±10%). Image content, compression behavior, and palette quantization are discrete, so exact bytes aren't always achievable.
- Q: Where are the files saved?
  - A: Next to the original inputs (Image/Rename tabs) or in the selected output directory (QR Code tab).
- Q: Can I make it faster?
  - A: Increase Workers if you have more CPU cores and RAM. For huge PDFs, try fewer Workers.
- Q: Do I need Ghostscript or gifsicle?
  - A: No. The app uses only the bundled ImageMagick `convert`.
- Q: How do I add custom rename patterns?
  - A: Go to the Rename tab, click "Add" next to "Enable Illegal Chars and Patterns" to open the pattern manager.
- Q: What does the "Add Orientation" option do?
  - A: When enabled, it detects each image's dimensions and adds L (Landscape), P (Portrait), or S (Square) to the filename as either a prefix or suffix.
- Q: What Excel format does the QR Code tab need?
  - A: Excel files should have columns named `name` (filename) and `url` (QR code data).

## Known Limitations
- Animated GIF creation from PDFs or image sequences is supported via ImageMagick but can be large; size-targeting relies on palette reduction and downscaling.
- Very aggressive targets may require substantial downscaling to meet.
- QR Code generation requires the `qrcode` and `PIL` (Pillow) libraries.

## Development Notes
- UI logic is split across modules: `app.py` (main), `renamer.py` (rename functionality), `qr_code.py` (QR generation).
- The app formerly supported `gifsicle`, but it's fully removed—now IM-only.
- Database fields are preserved across updates to maintain backward compatibility with existing settings.

## License
This software is owned by **Colin Parsons** and licensed exclusively for internal
use within **Inspired Thinking Group (ITG)**.

ITG colleagues may use, modify, and share the application internally. External
distribution, sharing, publishing, or sublicensing is not permitted without
prior written permission from the owner.

See the `LICENSE` file for full legal terms.