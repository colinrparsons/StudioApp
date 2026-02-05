"""
File Renamer Module
Contains the RenamerTab and PatternsDialog classes for the Rename tab functionality.
"""

import os
import re
import sqlite3
from PIL import Image
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QFileDialog, QLabel, QLineEdit, QComboBox, QCheckBox, 
    QDialog, QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt


class RenamerTab(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.file_paths = []  # To store original file paths
        self.previewed_names = []  # To store previewed file names

        layout = QVBoxLayout()

        # Label for instructions
        self.instructions = QLabel("Drag and drop files or use the Select Folder button.")
        layout.addWidget(self.instructions)

        # List widget to show changed file names
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        # Checkbox to enable illegal character and pattern replacement
        illegal_layout = QHBoxLayout()
        self.enable_illegal_chars = QCheckBox("Enable Illegal Chars and Patterns")
        self.enable_illegal_chars.setChecked(True)
        self.enable_illegal_chars.stateChanged.connect(self.on_illegal_chars_changed)
        illegal_layout.addWidget(self.enable_illegal_chars)
        
        self.add_pattern_button = QPushButton("Add")
        self.add_pattern_button.setFixedWidth(60)
        self.add_pattern_button.clicked.connect(self.open_patterns_dialog)
        illegal_layout.addWidget(self.add_pattern_button)
        illegal_layout.addStretch()
        layout.addLayout(illegal_layout)

        # Character replacement fields
        char_replacement_layout = QHBoxLayout()
        self.replace_char_label = QLabel("Replace:")
        self.replace_char_field = QLineEdit(" ")
        self.replace_char_field.textChanged.connect(self.on_replace_char_changed)
        self.with_char_label = QLabel("With:")
        self.with_char_field = QLineEdit("_")
        self.with_char_field.textChanged.connect(self.on_with_char_changed)
        char_replacement_layout.addWidget(self.replace_char_label)
        char_replacement_layout.addWidget(self.replace_char_field)
        char_replacement_layout.addWidget(self.with_char_label)
        char_replacement_layout.addWidget(self.with_char_field)
        layout.addLayout(char_replacement_layout)

        # Dropdown for case conversion
        button_layout = QHBoxLayout()
        self.case_dropdown = QComboBox()
        self.case_dropdown.addItems(["Default", "Capitals", "Title", "Lowercase"])
        self.case_dropdown.currentTextChanged.connect(self.on_case_changed)
        button_layout.addWidget(QLabel("Case Conversion:"))
        button_layout.addWidget(self.case_dropdown)

        # Orientation checkbox and position dropdown
        self.enable_orientation = QCheckBox("Add Orientation (L/P/S)")
        self.enable_orientation.setChecked(False)
        self.enable_orientation.stateChanged.connect(self.on_orientation_enabled_changed)
        button_layout.addWidget(self.enable_orientation)

        self.orientation_position = QComboBox()
        self.orientation_position.addItems(["Suffix", "Prefix"])
        self.orientation_position.setEnabled(False)
        self.orientation_position.currentTextChanged.connect(self.on_orientation_position_changed)
        button_layout.addWidget(self.orientation_position)

        # Buttons
        self.select_folder_button = QPushButton("Select Folder")
        self.select_folder_button.clicked.connect(self.select_folder)
        button_layout.addWidget(self.select_folder_button)

        self.clear_list_button = QPushButton("Clear List")
        self.clear_list_button.clicked.connect(self.clear_list)
        button_layout.addWidget(self.clear_list_button)

        self.process_button = QPushButton("Process")
        self.process_button.clicked.connect(self.process_files)
        button_layout.addWidget(self.process_button)

        self.export_button = QPushButton("Export to .txt")
        self.export_button.clicked.connect(self.export_to_txt)
        button_layout.addWidget(self.export_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Enable drag-and-drop functionality
        self.setAcceptDrops(True)

        # Load saved settings from database
        self.load_settings_from_db()

    def select_folder(self):
        """Open a dialog to select a folder and process its files."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", os.path.expanduser("~/Desktop"))
        if folder:
            self.file_paths = [os.path.join(root, file) for root, _, files in os.walk(folder) for file in files]
            self.update_preview()

    def update_preview(self):
        """Update the file list with previewed names."""
        self.file_list.clear()
        self.previewed_names = []
        for file_path in self.file_paths:
            original_filename = os.path.basename(file_path)
            cleaned_filename = self.preview_filename(file_path, original_filename)
            self.file_list.addItem(f"{original_filename} -> {cleaned_filename}")
            self.previewed_names.append(cleaned_filename)

    def preview_filename(self, file_path, filename):
        """Generate a preview of the new file name."""
        name, ext = os.path.splitext(filename)

        # Apply custom character replacement FIRST (before any other processing)
        replace_char = self.replace_char_field.text()
        with_char = self.with_char_field.text()
        if replace_char:
            name = name.replace(replace_char, with_char)

        # Apply illegal characters and patterns (if enabled)
        if self.enable_illegal_chars.isChecked():
            # Remove illegal chars but keep underscore and dash
            name = re.sub(r'[()+<>&|;"/\,!{@}£$^#€™|?*]', '', name)
            # Load and apply patterns from database
            patterns = self.load_patterns_from_db()
            for pattern, replacement in patterns:
                name = re.sub(pattern, replacement, name)
            # Collapse multiple consecutive underscores/dashes to single
            name = re.sub(r'_+', '_', name)
            name = re.sub(r'-+', '-', name)

        # Apply case conversion
        case_option = self.case_dropdown.currentText()
        if case_option == "Capitals":
            name = name.upper()
        elif case_option == "Title":
            name = name.title()
        elif case_option == "Lowercase":
            name = name.lower()

        # Apply orientation (if enabled)
        if self.enable_orientation.isChecked():
            orientation = self.get_image_orientation(file_path)
            if orientation:
                # Strip any existing orientation markers to prevent duplicates
                name = re.sub(r'(^[LPS]_)', '', name)  # Prefix patterns: L_, P_, S_
                name = re.sub(r'(_[LPS]$)', '', name)  # Suffix patterns: _L, _P, _S
                name = re.sub(r'_[LPS]_', '_', name)  # Middle patterns: _L_, _P_, _S_
                name = re.sub(r'_+', '_', name)  # Clean up any double underscores
                name = name.strip('_')  # Remove leading/trailing underscores
                
                position = self.orientation_position.currentText()
                if position == "Prefix":
                    name = f"{orientation}_{name}"
                else:  # Suffix
                    name = f"{name}_{orientation}"

        return name + ext

    def get_image_orientation(self, file_path):
        """Detect image orientation from file dimensions. Returns 'L', 'P', 'S', or None."""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                if width > height:
                    return 'L'  # Landscape
                elif height > width:
                    return 'P'  # Portrait
                else:
                    return 'S'  # Square
        except Exception:
            return None  # Not an image or error reading file

    def process_files(self):
        """Rename files based on the previewed names."""
        renamed_count = 0
        for original_path, new_name in zip(self.file_paths, self.previewed_names):
            new_path = os.path.join(os.path.dirname(original_path), new_name)
            if original_path != new_path:  # Only rename if actually different
                os.rename(original_path, new_path)
                renamed_count += 1
        # Update the list to show new names
        self.file_paths = [os.path.join(os.path.dirname(p), n) for p, n in zip(self.file_paths, self.previewed_names)]
        self.update_preview()
        self.instructions.setText(f"Renamed {renamed_count} files. List updated with new names.")

    def export_to_txt(self):
        """Export the previewed names to a .txt file using a save dialog."""
        if not self.file_paths:
            self.instructions.setText("No files to export. Add files first.")
            return
            
        # Open save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Rename List",
            os.path.expanduser("~/Desktop/Renamed_Files.txt"),
            "Text Files (*.txt)"
        )
        
        if not file_path:
            return  # User cancelled
            
        # Ensure .txt extension
        if not file_path.lower().endswith('.txt'):
            file_path += '.txt'
            
        try:
            with open(file_path, "w") as f:
                for original_path, new_name in zip(self.file_paths, self.previewed_names):
                    f.write(f"{os.path.basename(original_path)} -> {new_name}\n")
            self.instructions.setText(f"File names exported to {file_path}")
        except Exception as e:
            self.instructions.setText(f"Error exporting: {str(e)}")

    def clear_list(self):
        """Clear the file list."""
        self.file_list.clear()
        self.file_paths = []
        self.previewed_names = []

    def on_illegal_chars_changed(self):
        """Handle illegal chars checkbox change."""
        self.save_setting('enable_illegal', '1' if self.enable_illegal_chars.isChecked() else '0')
        self.update_preview()

    def on_replace_char_changed(self):
        """Handle replace char field change."""
        self.save_setting('replace_char', self.replace_char_field.text())
        self.update_preview()

    def on_with_char_changed(self):
        """Handle with char field change."""
        self.save_setting('with_char', self.with_char_field.text())
        self.update_preview()

    def on_case_changed(self):
        """Handle case dropdown change."""
        self.save_setting('case', self.case_dropdown.currentText())
        self.update_preview()

    def on_orientation_enabled_changed(self):
        """Handle orientation checkbox change."""
        self.save_setting('enable_orientation', '1' if self.enable_orientation.isChecked() else '0')
        self.orientation_position.setEnabled(self.enable_orientation.isChecked())
        self.update_preview()

    def on_orientation_position_changed(self):
        """Handle orientation position dropdown change."""
        self.save_setting('orientation_position', self.orientation_position.currentText())
        self.update_preview()

    def load_settings_from_db(self):
        """Load saved settings from the database."""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM settings WHERE key LIKE 'renamer_%'")
            settings = dict(cur.fetchall())
            conn.close()
            
            # Apply loaded settings
            if 'renamer_enable_illegal' in settings:
                self.enable_illegal_chars.setChecked(settings['renamer_enable_illegal'] == '1')
            if 'renamer_replace_char' in settings:
                self.replace_char_field.setText(settings['renamer_replace_char'])
            if 'renamer_with_char' in settings:
                self.with_char_field.setText(settings['renamer_with_char'])
            if 'renamer_case' in settings:
                self.case_dropdown.setCurrentText(settings['renamer_case'])
            if 'renamer_enable_orientation' in settings:
                self.enable_orientation.setChecked(settings['renamer_enable_orientation'] == '1')
                self.orientation_position.setEnabled(settings['renamer_enable_orientation'] == '1')
            if 'renamer_orientation_position' in settings:
                self.orientation_position.setCurrentText(settings['renamer_orientation_position'])
        except Exception:
            pass  # Use defaults if DB fails

    def save_setting(self, key: str, value: str):
        """Save a setting to the database using renamer_ prefix."""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            full_key = f"renamer_{key}"
            cur.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (full_key, value))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def open_patterns_dialog(self):
        """Open dialog to manage regex patterns."""
        dialog = PatternsDialog(self.database, self)
        dialog.exec_()
        # Refresh preview after dialog closes (patterns may have changed)
        self.update_preview()

    def get_default_patterns(self):
        """Return the default regex patterns."""
        return [
            (r'_x_', 'x'), (r'_X_', 'x'), (r'_~', '~'), (r'~_', '~'),
            (r'_px', 'px'), (r'_-_', '_'), (r' - ', '_'), (r' ', '_'),
            (r'--_', '_'), (r'_--', '_'), (r'%', 'pct'), (r'__+', '_'),
            (r'--+', '-'), (r'_mm', 'mm')
        ]

    def load_patterns_from_db(self):
        """Load patterns from database or return defaults if none saved."""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            # Check if patterns table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='renamer_patterns'")
            if cur.fetchone():
                cur.execute("SELECT pattern, replacement FROM renamer_patterns ORDER BY id")
                patterns = cur.fetchall()
                conn.close()
                if patterns:
                    return patterns
            conn.close()
        except Exception:
            pass
        return self.get_default_patterns()

    def save_patterns_to_db(self, patterns):
        """Save patterns to database."""
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            # Create table if not exists
            cur.execute('''CREATE TABLE IF NOT EXISTS renamer_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                replacement TEXT NOT NULL
            )''')
            # Clear existing patterns
            cur.execute("DELETE FROM renamer_patterns")
            # Insert new patterns
            for pattern, replacement in patterns:
                cur.execute("INSERT INTO renamer_patterns (pattern, replacement) VALUES (?, ?)",
                          (pattern, replacement))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving patterns: {e}")

    def dragEnterEvent(self, event):
        """Allow drag-and-drop of files and folders."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        """Handle dropped files and folders."""
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                self.file_paths.append(file_path)
            elif os.path.isdir(file_path):
                self.file_paths.extend([
                    os.path.join(root, file) for root, _, files in os.walk(file_path) for file in files
                ])
        self.update_preview()


class PatternsDialog(QDialog):
    """Dialog for managing regex patterns."""

    def __init__(self, database, parent=None):
        super().__init__(parent)
        self.database = database
        self.parent_tab = parent
        self.setWindowTitle("Manage Patterns")
        self.setGeometry(200, 200, 500, 400)

        layout = QVBoxLayout()

        # Instructions
        layout.addWidget(QLabel("Current Patterns (regex -> replacement):"))

        # Scroll area for patterns
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.patterns_widget = QWidget()
        self.patterns_layout = QVBoxLayout(self.patterns_widget)
        self.patterns_layout.setAlignment(Qt.AlignTop)
        scroll.setWidget(self.patterns_widget)
        layout.addWidget(scroll)

        # Add new pattern section
        add_layout = QHBoxLayout()
        add_layout.addWidget(QLabel("Pattern:"))
        self.new_pattern_input = QLineEdit()
        self.new_pattern_input.setPlaceholderText("e.g., _x_")
        add_layout.addWidget(self.new_pattern_input)
        add_layout.addWidget(QLabel("Replace with:"))
        self.new_replacement_input = QLineEdit()
        self.new_replacement_input.setPlaceholderText("e.g., x")
        add_layout.addWidget(self.new_replacement_input)

        add_btn = QPushButton("Add Pattern")
        add_btn.clicked.connect(self.add_new_pattern)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # Buttons
        button_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Load existing patterns
        self.load_patterns()

    def load_patterns(self):
        """Load and display patterns from database."""
        # Clear existing widgets
        while self.patterns_layout.count():
            item = self.patterns_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        patterns = self.parent_tab.load_patterns_from_db()

        for i, (pattern, replacement) in enumerate(patterns):
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{pattern}"))
            row.addWidget(QLabel("->"))
            row.addWidget(QLabel(f"'{replacement}'"))
            row.addStretch()

            remove_btn = QPushButton("-")
            remove_btn.setFixedWidth(30)
            remove_btn.clicked.connect(lambda checked, idx=i: self.remove_pattern(idx))
            row.addWidget(remove_btn)

            container = QWidget()
            container.setLayout(row)
            self.patterns_layout.addWidget(container)

    def add_new_pattern(self):
        """Add a new pattern to the list."""
        pattern = self.new_pattern_input.text().strip()
        replacement = self.new_replacement_input.text().strip()

        if not pattern:
            return

        # Load current patterns, add new one, save back
        patterns = self.parent_tab.load_patterns_from_db()
        patterns.append((pattern, replacement))
        self.parent_tab.save_patterns_to_db(patterns)

        # Clear inputs
        self.new_pattern_input.clear()
        self.new_replacement_input.clear()

        # Reload display
        self.load_patterns()

    def remove_pattern(self, index):
        """Remove a pattern at the given index."""
        patterns = self.parent_tab.load_patterns_from_db()
        if 0 <= index < len(patterns):
            patterns.pop(index)
            self.parent_tab.save_patterns_to_db(patterns)
            self.load_patterns()

    def reset_to_defaults(self):
        """Reset patterns to default values."""
        patterns = self.parent_tab.get_default_patterns()
        self.parent_tab.save_patterns_to_db(patterns)
        self.load_patterns()
