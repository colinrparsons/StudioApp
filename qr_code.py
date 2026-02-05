"""
QR Code Module
Contains the QRCodeTab class for generating QR codes from Excel data.
"""

import os
import io
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, 
    QFileDialog, QLabel, QLineEdit, QComboBox, QColorDialog, 
    QSpinBox, QMessageBox, QGroupBox, QGridLayout, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pandas as pd

try:
    import qrcode
    from qrcode.image.pil import PilImage
    from qrcode.image.svg import SvgImage, SvgFragmentImage, SvgPathImage
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class QRCodeTab(QWidget):
    def __init__(self, database):
        super().__init__()
        self.database = database
        self.df = None  # DataFrame for Excel data
        self.output_dir = os.path.expanduser("~/Desktop")
        
        self.init_ui()
        self.load_settings_from_db()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("QR Code Generator")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Excel Import/Export Group
        excel_group = QGroupBox("Excel Template")
        excel_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import Excel")
        self.import_btn.clicked.connect(self.import_excel)
        excel_layout.addWidget(self.import_btn)
        
        self.export_template_btn = QPushButton("Export Template")
        self.export_template_btn.clicked.connect(self.export_template)
        excel_layout.addWidget(self.export_template_btn)
        
        self.export_data_btn = QPushButton("Export Data")
        self.export_data_btn.clicked.connect(self.export_data)
        excel_layout.addWidget(self.export_data_btn)
        
        excel_layout.addStretch()
        excel_group.setLayout(excel_layout)
        layout.addWidget(excel_group)
        
        # Data Preview
        self.data_label = QLabel("No data loaded. Import an Excel file or create entries below.")
        layout.addWidget(self.data_label)
        
        self.data_list = QListWidget()
        self.data_list.setMaximumHeight(150)
        layout.addWidget(self.data_list)
        
        # Single QR Code Group
        single_group = QGroupBox("Single QR Code")
        single_layout = QGridLayout()
        
        single_layout.addWidget(QLabel("Name/Filename:"), 0, 0)
        self.single_name = QLineEdit()
        self.single_name.setPlaceholderText("e.g., my_qrcode")
        single_layout.addWidget(self.single_name, 0, 1)
        
        single_layout.addWidget(QLabel("URL:"), 1, 0)
        self.single_url = QLineEdit()
        self.single_url.setPlaceholderText("e.g., https://example.com")
        single_layout.addWidget(self.single_url, 1, 1)
        
        self.add_single_btn = QPushButton("Add to List")
        self.add_single_btn.clicked.connect(self.add_single_entry)
        single_layout.addWidget(self.add_single_btn, 2, 1)
        
        single_group.setLayout(single_layout)
        layout.addWidget(single_group)
        
        # QR Code Settings Group
        settings_group = QGroupBox("QR Code Settings")
        settings_layout = QGridLayout()
        
        # Output format
        settings_layout.addWidget(QLabel("Output Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "SVG", "TIFF", "EPS", "PDF"])
        settings_layout.addWidget(self.format_combo, 0, 1)
        
        # QR Code size
        settings_layout.addWidget(QLabel("Size (boxes):"), 1, 0)
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 40)
        self.size_spin.setValue(10)
        settings_layout.addWidget(self.size_spin, 1, 1)
        
        # Border size
        settings_layout.addWidget(QLabel("Border (boxes):"), 2, 0)
        self.border_spin = QSpinBox()
        self.border_spin.setRange(0, 10)
        self.border_spin.setValue(4)
        settings_layout.addWidget(self.border_spin, 2, 1)
        
        # Error correction
        settings_layout.addWidget(QLabel("Error Correction:"), 3, 0)
        self.error_combo = QComboBox()
        self.error_combo.addItems(["Low (L)", "Medium (M)", "Quartile (Q)", "High (H)"])
        settings_layout.addWidget(self.error_combo, 3, 1)
        
        # Colors
        settings_layout.addWidget(QLabel("Fill Color:"), 4, 0)
        self.fill_color_btn = QPushButton("#000000")
        self.fill_color_btn.clicked.connect(lambda: self.pick_color(self.fill_color_btn))
        self.fill_color = "#000000"
        settings_layout.addWidget(self.fill_color_btn, 4, 1)
        
        settings_layout.addWidget(QLabel("Background Color:"), 5, 0)
        self.bg_color_btn = QPushButton("#FFFFFF")
        self.bg_color_btn.clicked.connect(lambda: self.pick_color(self.bg_color_btn))
        self.bg_color = "#FFFFFF"
        settings_layout.addWidget(self.bg_color_btn, 5, 1)
        
        # Transparent background checkbox
        self.transparent_bg = QCheckBox("Transparent Background")
        self.transparent_bg.stateChanged.connect(self.on_transparent_changed)
        settings_layout.addWidget(self.transparent_bg, 6, 0, 1, 2)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Output directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output Directory:"))
        self.dir_label = QLabel(self.output_dir)
        self.dir_label.setStyleSheet("color: gray;")
        dir_layout.addWidget(self.dir_label, 1)
        
        self.change_dir_btn = QPushButton("Change...")
        self.change_dir_btn.clicked.connect(self.change_output_dir)
        dir_layout.addWidget(self.change_dir_btn)
        layout.addLayout(dir_layout)
        
        # Generate buttons
        btn_layout = QHBoxLayout()
        
        self.generate_single_btn = QPushButton("Generate Single")
        self.generate_single_btn.clicked.connect(self.generate_single)
        btn_layout.addWidget(self.generate_single_btn)
        
        self.generate_batch_btn = QPushButton("Generate Batch (All)")
        self.generate_batch_btn.clicked.connect(self.generate_batch)
        btn_layout.addWidget(self.generate_batch_btn)
        
        self.clear_btn = QPushButton("Clear List")
        self.clear_btn.clicked.connect(self.clear_list)
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def pick_color(self, button):
        color = QColorDialog.getColor(QColor(button.text()), self)
        if color.isValid():
            button.setText(color.name())
            if button == self.fill_color_btn:
                self.fill_color = color.name()
            else:
                self.bg_color = color.name()
    
    def on_transparent_changed(self, state):
        """Handle transparent background checkbox change."""
        if state == Qt.Checked:
            self.bg_color_btn.setEnabled(False)
            self.bg_color = "transparent"
        else:
            self.bg_color_btn.setEnabled(True)
            self.bg_color = self.bg_color_btn.text()
        self.save_setting('qr_transparent_bg', '1' if state == Qt.Checked else '0')
    
    def change_output_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir)
        if folder:
            self.output_dir = folder
            self.dir_label.setText(folder)
            self.save_setting('qr_output_dir', folder)
    
    def import_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if not file_path:
            return
        
        try:
            self.df = pd.read_excel(file_path)
            if 'name' not in self.df.columns or 'url' not in self.df.columns:
                if 'filename' in self.df.columns:
                    self.df.rename(columns={'filename': 'name'}, inplace=True)
                else:
                    QMessageBox.warning(self, "Invalid Format", 
                        "Excel must have 'name' and 'url' columns (or 'filename' and 'url').")
                    return
            self.update_data_list()
            self.status_label.setText(f"Imported {len(self.df)} entries from Excel.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import Excel: {str(e)}")
    
    def export_template(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Template", 
            os.path.join(self.output_dir, "qr_template.xlsx"),
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        
        try:
            template_df = pd.DataFrame({
                'name': ['example_qr', 'sample_code'],
                'url': ['https://example.com', 'https://sample.org']
            })
            template_df.to_excel(file_path, index=False)
            self.status_label.setText(f"Template exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export template: {str(e)}")
    
    def export_data(self):
        if self.df is None or len(self.df) == 0:
            QMessageBox.information(self, "No Data", "No data to export. Import or add entries first.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Data",
            os.path.join(self.output_dir, "qr_data.xlsx"),
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return
        
        try:
            self.df.to_excel(file_path, index=False)
            self.status_label.setText(f"Data exported to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
    
    def add_single_entry(self):
        name = self.single_name.text().strip()
        url = self.single_url.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "Missing Data", "Please enter both name and URL.")
            return
        
        if self.df is None:
            self.df = pd.DataFrame(columns=['name', 'url'])
        
        new_row = pd.DataFrame({'name': [name], 'url': [url]})
        self.df = pd.concat([self.df, new_row], ignore_index=True)
        
        self.single_name.clear()
        self.single_url.clear()
        self.update_data_list()
        self.status_label.setText(f"Added: {name}")
    
    def update_data_list(self):
        self.data_list.clear()
        if self.df is not None and len(self.df) > 0:
            for _, row in self.df.iterrows():
                self.data_list.addItem(f"{row['name']} -> {row['url']}")
            self.data_label.setText(f"{len(self.df)} entries loaded:")
        else:
            self.data_label.setText("No data loaded.")
    
    def clear_list(self):
        self.df = None
        self.data_list.clear()
        self.data_label.setText("No data loaded.")
        self.status_label.setText("List cleared.")
    
    def get_error_correction(self):
        level = self.error_combo.currentText()
        if not QR_AVAILABLE:
            return None
        if "Low" in level:
            return qrcode.constants.ERROR_CORRECT_L
        elif "Medium" in level:
            return qrcode.constants.ERROR_CORRECT_M
        elif "Quartile" in level:
            return qrcode.constants.ERROR_CORRECT_Q
        else:
            return qrcode.constants.ERROR_CORRECT_H
    
    def generate_qr(self, name, url, filepath):
        if not QR_AVAILABLE:
            raise ImportError("qrcode library not installed. Run: pip install qrcode[pil]")
        
        fmt = self.format_combo.currentText().lower()
        transparent = self.bg_color == "transparent"
        
        # Create QR code instance
        qr = qrcode.QRCode(
            version=None,
            error_correction=self.get_error_correction(),
            box_size=self.size_spin.value(),
            border=self.border_spin.value(),
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Generate image based on format
        if fmt == 'svg':
            # SVG doesn't support transparency in the same way, use white background
            bg = self.bg_color if not transparent else "white"
            img = qr.make_image(image_factory=SvgPathImage, fill_color=self.fill_color, back_color=bg)
            img.save(filepath)
        elif fmt == 'png' and transparent and PIL_AVAILABLE:
            # For PNG with transparency, create RGBA image
            img = qr.make_image(image_factory=PilImage, fill_color=self.fill_color, back_color="white")
            # Convert to RGBA and make white background transparent
            img = img.convert('RGBA')
            datas = img.getdata()
            newData = []
            for item in datas:
                # Change all white (also shades of white) pixels to transparent
                if item[0] > 200 and item[1] > 200 and item[2] > 200:
                    newData.append((255, 255, 255, 0))
                else:
                    newData.append(item)
            img.putdata(newData)
            img.save(filepath, 'PNG')
        elif fmt in ('eps', 'tiff', 'pdf'):
            if not PIL_AVAILABLE:
                raise ImportError("PIL not available")
            bg = self.bg_color if not transparent else "white"
            img = qr.make_image(fill_color=self.fill_color, back_color=bg)
            fmt_upper = fmt.upper()
            img.save(filepath, fmt_upper)
        else:  # png default (non-transparent)
            if not PIL_AVAILABLE:
                raise ImportError("PIL not available")
            img = qr.make_image(fill_color=self.fill_color, back_color=self.bg_color)
            img.save(filepath, 'PNG')
    
    def generate_single(self):
        name = self.single_name.text().strip()
        url = self.single_url.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "Missing Data", "Please enter both name and URL.")
            return
        
        fmt = self.format_combo.currentText().lower()
        filepath = os.path.join(self.output_dir, f"{name}.{fmt}")
        
        try:
            self.generate_qr(name, url, filepath)
            self.status_label.setText(f"Generated: {filepath}")
            self.single_name.clear()
            self.single_url.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate QR: {str(e)}")
    
    def generate_batch(self):
        if self.df is None or len(self.df) == 0:
            QMessageBox.information(self, "No Data", "No data to process. Import or add entries first.")
            return
        
        fmt = self.format_combo.currentText().lower()
        success_count = 0
        errors = []
        
        for _, row in self.df.iterrows():
            name = str(row['name']).strip()
            url = str(row['url']).strip()
            
            if not name or not url:
                continue
            
            # Clean filename
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_name = safe_name.replace(' ', '_')
            
            filepath = os.path.join(self.output_dir, f"{safe_name}.{fmt}")
            
            try:
                self.generate_qr(name, url, filepath)
                success_count += 1
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
        
        if errors:
            self.status_label.setText(f"Generated {success_count}/{len(self.df)}. Some errors occurred.")
            QMessageBox.warning(self, "Batch Complete", 
                f"Generated {success_count} of {len(self.df)} QR codes.\n\nErrors:\n" + "\n".join(errors[:5]))
        else:
            self.status_label.setText(f"Generated {success_count} QR codes successfully!")
    
    def load_settings_from_db(self):
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            cur.execute("SELECT key, value FROM settings WHERE key LIKE 'qr_%'")
            settings = dict(cur.fetchall())
            conn.close()
            
            if 'qr_output_dir' in settings:
                self.output_dir = settings['qr_output_dir']
                self.dir_label.setText(self.output_dir)
            if 'qr_format' in settings:
                self.format_combo.setCurrentText(settings['qr_format'])
            if 'qr_size' in settings:
                self.size_spin.setValue(int(settings['qr_size']))
            if 'qr_border' in settings:
                self.border_spin.setValue(int(settings['qr_border']))
            if 'qr_fill_color' in settings:
                self.fill_color = settings['qr_fill_color']
                self.fill_color_btn.setText(self.fill_color)
            if 'qr_bg_color' in settings:
                self.bg_color = settings['qr_bg_color']
                self.bg_color_btn.setText(self.bg_color)
            if 'qr_transparent_bg' in settings:
                is_transparent = settings['qr_transparent_bg'] == '1'
                self.transparent_bg.setChecked(is_transparent)
                if is_transparent:
                    self.bg_color_btn.setEnabled(False)
                    self.bg_color = "transparent"
        except Exception:
            pass
    
    def save_setting(self, key, value):
        try:
            conn = sqlite3.connect(self.database)
            cur = conn.cursor()
            full_key = f"qr_{key}"
            cur.execute("INSERT INTO settings(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (full_key, value))
            conn.commit()
            conn.close()
        except Exception:
            pass
