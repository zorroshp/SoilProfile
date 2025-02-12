"""
Module: soilpro.py
This is the main application module for SoilPro.
It integrates the input table, profile plotting, and PDF export functionalities into a unified PyQt5 GUI.
"""

from library import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFrame, QMessageBox, QTableWidgetItem, QIcon
)
from library import FigureCanvas, NavigationToolbar
import csv
import matplotlib.pyplot as plt

from input_table import InputTable
from plotter import extract_borehole_data, generate_borehole_profile_plot
from pdf_export import export_scaled_pdf
from app_data import convert_to_lighter, COLOR_PALETTES

class SoilPro(QMainWindow):
    """
    Main window class for SoilPro.
    Provides an interface to import borehole data, generate soil profile plots,
    and export a scaled PDF.
    """
    SCALE_OPTIONS = ["1:10", "1:25", "1:50", "1:75", "1:100", "1:150", "1:200", "1:250", "1:300", "1:400", "1:500", "1:1000"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoilPro")
        self.setWindowIcon(QIcon("soilpro_icon.png"))
        self.setGeometry(50, 50, 1600, 950)
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the main GUI layout.
        """
        main_splitter = QSplitter()

        # Left panel: Borehole information, CSV import, and input tables.
        left_panel = QWidget()
        left_panel.setMinimumWidth(480)
        left_panel.setMaximumWidth(485)
        left_layout = QVBoxLayout(left_panel)

        # Borehole Information Group
        borehole_info_group = QGroupBox("Borehole Information")
        borehole_info_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        borehole_info_layout = QVBoxLayout()
        self.borehole1_name_edit = QLineEdit("Borehole-1")
        self.borehole2_name_edit = QLineEdit("Borehole-2")
        borehole_info_layout.addWidget(QLabel("Borehole Names:"))
        borehole_info_layout.addWidget(self.borehole1_name_edit)
        borehole_info_layout.addWidget(self.borehole2_name_edit)
        borehole_info_group.setLayout(borehole_info_layout)
        left_layout.addWidget(borehole_info_group)

        # CSV Import Button
        import_csv_button = QPushButton("Import CSV")
        import_csv_button.clicked.connect(self.import_csv)
        left_layout.addWidget(import_csv_button)

        # Borehole Data Tables Group
        data_group = QGroupBox("Borehole Data")
        data_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        data_layout = QVBoxLayout()
        data_layout.addWidget(QLabel("Borehole 1 Data:"))
        self.borehole1_table = InputTable()
        data_layout.addWidget(self.borehole1_table)
        data_layout.addWidget(QLabel("Borehole 2 Data:"))
        self.borehole2_table = InputTable()
        data_layout.addWidget(self.borehole2_table)
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)

        # Right panel: Plot canvas and settings.
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)

        # Generate Profile Button
        generate_profile_button = QPushButton("Generate Profile")
        generate_profile_button.clicked.connect(self.generate_plot)
        right_layout.addWidget(generate_profile_button)

        # Plot Settings Group
        settings_group = QGroupBox("Plot Settings")
        settings_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        settings_layout = QVBoxLayout()

        # Color Palette Settings
        palette_group = QGroupBox("Color Palette")
        palette_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        palette_layout = QHBoxLayout()
        palette_layout.setSpacing(10)
        palette_layout.addWidget(QLabel("Select Palette:"))
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(list(COLOR_PALETTES.keys()))
        palette_layout.addWidget(self.palette_combo)
        self.halftone_checkbox = QCheckBox("Halftone")
        self.halftone_checkbox.setChecked(False)
        palette_layout.addWidget(self.halftone_checkbox)
        palette_group.setLayout(palette_layout)
        settings_layout.addWidget(palette_group)

        # Grid Settings
        grid_group = QGroupBox("Grid Settings")
        grid_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        grid_layout = QHBoxLayout()
        grid_layout.setSpacing(10)
        self.grid_checkbox = QCheckBox("Level Grids")
        self.grid_checkbox.setChecked(True)
        grid_layout.addWidget(self.grid_checkbox)
        grid_layout.addWidget(QLabel("Grid Interval (m):"))
        self.grid_interval_spinbox = QDoubleSpinBox()
        self.grid_interval_spinbox.setRange(0.1, 10.0)
        self.grid_interval_spinbox.setValue(1.0)
        self.grid_interval_spinbox.setSingleStep(0.1)
        self.grid_interval_spinbox.setMaximumWidth(60)
        grid_layout.addWidget(self.grid_interval_spinbox)
        self.grid_label_checkbox = QCheckBox("Grid Labels")
        self.grid_label_checkbox.setChecked(True)
        grid_layout.addWidget(self.grid_label_checkbox)
        grid_group.setLayout(grid_layout)
        grid_group.setContentsMargins(10, 10, 10, 10)
        settings_layout.addWidget(grid_group)

        # Font Size Settings
        font_group = QGroupBox("Font Sizes")
        font_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font_layout = QHBoxLayout()
        font_layout.setSpacing(10)
        font_layout.addWidget(QLabel("Detail:"))
        self.detail_font_size_spinbox = QSpinBox()
        self.detail_font_size_spinbox.setRange(1, 50)
        self.detail_font_size_spinbox.setValue(9)
        self.detail_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.detail_font_size_spinbox)
        font_layout.addWidget(QLabel("Grid:"))
        self.grid_font_size_spinbox = QSpinBox()
        self.grid_font_size_spinbox.setRange(1, 50)
        self.grid_font_size_spinbox.setValue(8)
        self.grid_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.grid_font_size_spinbox)
        font_layout.addWidget(QLabel("Title:"))
        self.title_font_size_spinbox = QSpinBox()
        self.title_font_size_spinbox.setRange(1, 50)
        self.title_font_size_spinbox.setValue(12)
        self.title_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.title_font_size_spinbox)
        font_layout.addWidget(QLabel("Level:"))
        self.level_font_size_spinbox = QSpinBox()
        self.level_font_size_spinbox.setRange(1, 50)
        self.level_font_size_spinbox.setValue(10)
        self.level_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.level_font_size_spinbox)
        font_group.setLayout(font_layout)
        settings_layout.addWidget(font_group)

        # Profile Dimensions Settings
        dimensions_group = QGroupBox("Profile Dimensions")
        dimensions_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        dimensions_layout = QHBoxLayout()
        dimensions_layout.setSpacing(10)
        dimensions_layout.addWidget(QLabel("Profile Width (m):"))
        self.profile_width_spinbox = QSpinBox()
        self.profile_width_spinbox.setRange(1, 100)
        self.profile_width_spinbox.setValue(2)
        dimensions_layout.addWidget(self.profile_width_spinbox)
        dimensions_layout.addWidget(QLabel("Borehole Spacing (m):"))
        self.borehole_spacing_spinbox = QSpinBox()
        self.borehole_spacing_spinbox.setRange(0, 100)
        self.borehole_spacing_spinbox.setValue(15)
        dimensions_layout.addWidget(self.borehole_spacing_spinbox)
        dimensions_group.setLayout(dimensions_layout)
        settings_layout.addWidget(dimensions_group)

        # Scaled PDF Export Settings
        pdf_group = QGroupBox("Scaled PDF Export")
        pdf_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        pdf_layout = QHBoxLayout()
        pdf_layout.addWidget(QLabel("Paper:"))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["A0", "A1", "A3", "A4", "Letter"])
        pdf_layout.addWidget(self.paper_combo)
        pdf_layout.addWidget(QLabel("Orientation:"))
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["Portrait", "Landscape"])
        pdf_layout.addWidget(self.orientation_combo)
        pdf_layout.addWidget(QLabel("Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(self.SCALE_OPTIONS)
        pdf_layout.addWidget(self.scale_combo)
        save_pdf_button = QPushButton("Save PDF (Scaled)")
        save_pdf_button.clicked.connect(self.export_pdf)
        pdf_layout.addWidget(save_pdf_button)
        pdf_group.setLayout(pdf_layout)
        settings_layout.addWidget(pdf_group)

        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        self.setCentralWidget(main_splitter)

    def import_csv(self):
        """
        Import borehole data from a CSV file.
        Expected columns: Borehole, Layer No, Layer Name, Start Level (m), End Level (m), SPT Value.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not filename:
            return
        try:
            with open(filename, 'r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row.get('Borehole') == '1':
                        table = self.borehole1_table
                    else:
                        table = self.borehole2_table
                    layer_no = int(row.get('Layer No', 1)) - 1
                    while table.rowCount() <= layer_no:
                        table.insertRow(table.rowCount())
                    table.setItem(layer_no, 0, QTableWidgetItem(row.get('Layer Name', '')))
                    table.setItem(layer_no, 1, QTableWidgetItem(row.get('Start Level (m)', '')))
                    table.setItem(layer_no, 2, QTableWidgetItem(row.get('End Level (m)', '')))
                    table.setItem(layer_no, 3, QTableWidgetItem(row.get('SPT Value', '')))
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"CSV Error: {str(e)}")

    def generate_plot(self):
        """
        Generate the soil profile plot from the input table data.
        """
        borehole1_data = extract_borehole_data(self.borehole1_table)
        borehole2_data = extract_borehole_data(self.borehole2_table)
        borehole_names = (self.borehole1_name_edit.text(), self.borehole2_name_edit.text())
        font_sizes = {
            'title': self.title_font_size_spinbox.value(),
            'stack_bar': self.detail_font_size_spinbox.value(),
            'borehole_level': self.level_font_size_spinbox.value()
        }
        grid_settings = {
            'grid': self.grid_checkbox.isChecked(),
            'grid_interval': self.grid_interval_spinbox.value(),
            'grid_label': self.grid_label_checkbox.isChecked(),
            'grid_label_font_size': self.grid_font_size_spinbox.value()
        }
        palette_name = self.palette_combo.currentText()
        generate_borehole_profile_plot(
            self.figure, borehole1_data, borehole2_data, borehole_names,
            self.profile_width_spinbox.value(), self.borehole_spacing_spinbox.value(),
            font_sizes, grid_settings, palette_name,
            COLOR_PALETTES, self.halftone_checkbox.isChecked(),
            convert_to_lighter
        )

    def export_pdf(self):
        """
        Export the current soil profile plot to a scaled PDF.
        """
        borehole1_data = extract_borehole_data(self.borehole1_table)
        borehole2_data = extract_borehole_data(self.borehole2_table)
        if not (borehole1_data or borehole2_data):
            QMessageBox.warning(self, "No Data", "No borehole data found.")
            return
        borehole_names = (self.borehole1_name_edit.text(), self.borehole2_name_edit.text())
        font_sizes = {
            'title': self.title_font_size_spinbox.value(),
            'stack_bar': self.detail_font_size_spinbox.value(),
            'borehole_level': self.level_font_size_spinbox.value()
        }
        grid_settings = {
            'grid': self.grid_checkbox.isChecked(),
            'grid_interval': self.grid_interval_spinbox.value(),
            'grid_label': self.grid_label_checkbox.isChecked(),
            'grid_label_font_size': self.grid_font_size_spinbox.value()
        }
        palette_name = self.palette_combo.currentText()
        scale_str = self.scale_combo.currentText()
        paper = self.paper_combo.currentText()
        orientation = self.orientation_combo.currentText()
        output_filename, _ = QFileDialog.getSaveFileName(self, "Save PDF (Scaled)", "", "PDF Files (*.pdf)")
        if not output_filename:
            return
        try:
            success = export_scaled_pdf(
                borehole1_data, borehole2_data, borehole_names,
                self.profile_width_spinbox.value(), self.borehole_spacing_spinbox.value(),
                scale_str, paper, orientation,
                font_sizes, grid_settings,
                palette_name, COLOR_PALETTES,
                self.halftone_checkbox.isChecked(),
                convert_to_lighter, output_filename
            )
            if success:
                QMessageBox.information(self, "Saved PDF", f"Saved scaled PDF to: {output_filename}")
        except Exception as e:
            QMessageBox.warning(self, "Save PDF Error", f"Could not save PDF: {str(e)}")

if __name__ == "__main__":
    app = QApplication([])
    window = SoilPro()
    window.show()
    app.exec_()
