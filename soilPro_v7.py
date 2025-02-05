import sys
import csv
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QLineEdit,
    QFileDialog, QComboBox, QCheckBox, QDoubleSpinBox, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard, QIcon, QFont
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

################################################################################
# Additional constants and helpers for scaled PDF export
################################################################################

PAPER_SIZES_INCHES = {
    "A0":     (33.11, 46.81),   # 841 x 1189 mm in inches
    "A1":     (23.39, 33.11),   # 594 x 841 mm in inches
    "A3":     (11.69, 16.54),
    "A4":     (8.27, 11.69),
    "Letter": (8.5,  11.0),
}
def convert_to_lighter(hex_color, factor=0.5):
    """
    Convert a hex color (e.g. '#RRGGBB') to a lighter version by blending with white.
    """
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    lr = int(r + (255 - r) * factor)
    lg = int(g + (255 - g) * factor)
    lb = int(b + (255 - b) * factor)
    return f"#{lr:02x}{lg:02x}{lb:02x}"

class EnhancedTable(QTableWidget):
    """
    Custom QTableWidget with enhanced features:
      - Predefined headers and column widths.
      - Right-click context menu for copying, pasting, and clearing cells.
    """
    HEADER_HEIGHT = 40
    COLUMN_WIDTHS = [120, 80, 80, 80]
    COLUMN_PADDING = 10

    def __init__(self, parent=None):
        super().__init__(15, 4)
        self.setup_table()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def setup_table(self):
        """Set up the table with headers and predefined column widths."""
        headers = ["Layer\nName", "Start\nLevel (m)", "End\nLevel (m)", "SPT\nValue"]
        self.setHorizontalHeaderLabels(headers)
        header = self.horizontalHeader()
        header.setFixedHeight(self.HEADER_HEIGHT)
        header.setDefaultAlignment(Qt.AlignCenter)
        for col, width in enumerate(self.COLUMN_WIDTHS):
            self.setColumnWidth(col, width + self.COLUMN_PADDING)
        header.setStyleSheet("""
            QHeaderView::section {
                border: 1px solid #ddd;
                padding: 4px;
                font-weight: normal;
            }
        """)
        # Adjust row height – change the value here to set the height for all rows.
        self.verticalHeader().setDefaultSectionSize(30)

    def context_menu(self, position):
        menu = QMenu()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        delete_action = menu.addAction("Clear")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == copy_action:
            self.copy_selection()
        elif action == paste_action:
            self.paste_selection()
        elif action == delete_action:
            self.clear_selection()

    def copy_selection(self):
        selected = self.selectedRanges()
        if not selected:
            return
        text = ""
        for r in selected:
            for row in range(r.topRow(), r.bottomRow() + 1):
                for col in range(r.leftColumn(), r.rightColumn() + 1):
                    item = self.item(row, col)
                    text += (item.text() if item else "") + "\t"
                text = text.rstrip() + "\n"
        self.clipboard.setText(text.strip())

    def paste_selection(self):
        text = self.clipboard.text()
        rows = text.split("\n")
        current_row = self.currentRow()
        current_col = self.currentColumn()
        for r, row in enumerate(rows):
            cells = row.split("\t")
            for c, cell in enumerate(cells):
                row_pos = current_row + r
                col_pos = current_col + c
                if row_pos < self.rowCount() and col_pos < self.columnCount():
                    self.setItem(row_pos, col_pos, QTableWidgetItem(cell.strip()))

    def clear_selection(self):
        for item in self.selectedItems():
            item.setText("")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.clear_selection()
        else:
            super().keyPressEvent(event)

class SoilProfileApp(QMainWindow):
    """
    Main application window for the Geotechnical Profile Analyzer.
    Includes original logic for on-screen preview and a new scaled PDF export.
    """
    COLOR_PALETTES = {
        "Geotech 12": [
            '#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6',
            '#4292c6', '#2171b5', '#08519c', '#08306b', '#082252',
            '#081538', '#080c1e'
        ],
        "Earth tones": [
            '#fff7bc', '#fee391', '#fec44f', '#fe9929', '#ec7014',
            '#cc4c02', '#993404', '#662506', '#4d1c02', '#331302',
            '#1a0a01', '#000000'
        ],
        "Clay": [
            '#FDF4E3', '#FCEAD1', '#FBD0B9', '#F9B6A1', '#F89C89',
            '#F78271', '#F56859', '#F34E41', '#F13429', '#EE1A11',
            '#EC0000', '#D40000'
        ],
        "Rock": [
            '#EDEDED', '#DBDBDB', '#C9C9C9', '#B7B7B7', '#A5A5A5',
            '#939393', '#818181', '#6F6F6F', '#5D5D5D', '#4B4B4B',
            '#393939', '#272727'
        ],
        "Organic": [
            '#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A',
            '#4CAF50', '#43A047', '#388E3C', '#2E7D32', '#1B5E20',
            '#0D4F10', '#003300'
        ],
        "Terra Firma": [
            '#F7F1E1', '#EEDCC0', '#E4C69F', '#DAB07E', '#D0955E',
            '#C67A3D', '#BA603C', '#AE463B', '#A42C3A', '#991238',
            '#8F0037', '#850036'
        ],
        "Neon Circuit Burst": [
            '#39FF14', '#2EFEF7', '#FF073A', '#F7FE2E', '#FE2EC8',
            '#FF8000', '#FF1493', '#00BFFF', '#7FFF00', '#FF4500',
            '#ADFF2F', '#FF69B4'
        ],
        "elemental harmony": [
            '#DFF0E1', '#BCE0C9', '#99D1B1', '#76C299', '#53B381',
            '#30A269', '#0D9351', '#0A7C45', '#075C38', '#04472C',
            '#03331F', '#022015'
        ],
        "Blue Agent": [
            '#E0F7FA', '#B2EBF2', '#80DEEA', '#4DD0E1', '#26C6DA',
            '#00BCD4', '#00ACC1', '#0097A7', '#00838F', '#006064',
            '#004D40', '#00332E'
        ],
        "Desert Ember": [
            '#FFF4E6', '#FFE8CC', '#FFDBB3', '#FFCF99', '#FFC27F',
            '#FFB766', '#FFAA4D', '#FF9E33', '#FF921A', '#FF8500',
            '#E67A00', '#CC6F00'
        ],
        "Harvest Harmony": [
            '#FFF8E1', '#FFECB3', '#FFE082', '#FFD54F', '#FFCA28',
            '#FFC107', '#FFB300', '#FFA000', '#FF8F00', '#FF6F00',
            '#E65100', '#BF360C'
        ],
        "Finn": [
            '#E8EAF6', '#C5CAE9', '#9FA8DA', '#7986CB', '#5C6BC0',
            '#3F51B5', '#3949AB', '#303F9F', '#283593', '#1A237E',
            '#121858', '#0D1240'
        ],
        "Disturbed": [
            '#FDEBD0', '#FAD7A0', '#F8C471', '#F5B041', '#F39C12',
            '#E67A22', '#D35400', '#BA4A00', '#A04000', '#873600',
            '#6E2C00', '#562200'
        ],
        "Urban Slate": [
            '#E0E0E0', '#C0C0C0', '#A0A0A0', '#808080', '#606060',
            '#404040', '#202020', '#1F1F1F', '#1A1A1A', '#141414',
            '#0F0F0F', '#0A0A0A'
        ],
        "Canyon Dust": [
            '#F4E1D2', '#E8D1B8', '#DCBF9E', '#D0AD84', '#C49B6A',
            '#B88850', '#AD7526', '#A1610C', '#965000', '#8A3F00',
            '#7F2E00', '#732D00'
        ],
        "Red Shift": [
            "#FF0000", "#FF8000", "#FFFF00", "#BFFF00", "#80FF00", "#00FF00",
            "#00FF80", "#00BFFF", "#0000FF", "#4000BF", "#600099", "#800080"
        ],
        "Reverse Red Shift": [
            "#800080", "#600099", "#4000BF", "#0000FF", "#00BFFF", "#00FF80",
            "#00FF00", "#80FF00", "#BFFF00", "#FFFF00", "#FF8000", "#FF0000"
        ]
    }
    SCALE_OPTIONS = ["1:10", "1:25", "1:50", "1:75", "1:100","1:150","1:200","1:250","1:300","1:400","1:500","1:1000"]

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowTitle("SoilPro")
        self.setWindowIcon(QIcon("soilpro_icon.png"))
        self.setGeometry(50, 50, 1600, 950)

    def init_ui(self):
        """Set up a modern, user-friendly GUI layout."""
        main_splitter = QSplitter(Qt.Horizontal)

        # Left Panel Setup (Borehole Info, Import CSV, Borehole Data)
        left_panel = QWidget()
        left_panel.setMinimumWidth(480)
        left_panel.setMaximumWidth(485)
        left_layout = QVBoxLayout(left_panel)

        # Borehole Information Section
        borehole_group = QGroupBox("Borehole Information")
        borehole_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        borehole_layout = QVBoxLayout()
        self.bh1_name = QLineEdit("Borehole-1")
        self.bh2_name = QLineEdit("Borehole-2")
        borehole_layout.addWidget(QLabel("Borehole Names:"))
        borehole_layout.addWidget(self.bh1_name)
        borehole_layout.addWidget(self.bh2_name)
        borehole_group.setLayout(borehole_layout)
        left_layout.addWidget(borehole_group)

        # Import CSV Button
        left_layout.addWidget(QPushButton("Import CSV", clicked=self.import_csv))

        # Borehole Data Tables
        data_group = QGroupBox("Borehole Data")
        data_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        data_layout = QVBoxLayout()
        data_layout.addWidget(QLabel("Borehole 1 Data:"))
        self.bh1_table = EnhancedTable()
        data_layout.addWidget(self.bh1_table)
        data_layout.addWidget(QLabel("Borehole 2 Data:"))
        self.bh2_table = EnhancedTable()
        data_layout.addWidget(self.bh2_table)
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)


        # Right Panel (Plot + Settings)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)

        # Generate Profile Button
        right_layout.addWidget(QPushButton("Generate Profile", clicked=self.generate_plot))

        # Plot Settings Section
        plot_settings_group = QGroupBox("Plot Settings")
        plot_settings_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        plot_settings_layout = QVBoxLayout()

        # Color Palette
        cp_group = QGroupBox("Color Palette")
        cp_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        cp_layout = QHBoxLayout()
        cp_layout.setSpacing(10)
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        self.halftone_checkbox = QCheckBox("Halftone")
        self.halftone_checkbox.setChecked(False)
        cp_layout.addWidget(QLabel("Select Palette:"))
        cp_layout.addWidget(self.palette_selector)
        cp_layout.addWidget(self.halftone_checkbox)
        cp_group.setLayout(cp_layout)
        plot_settings_layout.addWidget(cp_group)

        # Horizontal line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line1)

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
        plot_settings_layout.addWidget(grid_group)

        # Horizontal line
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line2)

        # Font Sizes
        font_group = QGroupBox("Font Sizes")
        font_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font_layout = QHBoxLayout()
        font_layout.setSpacing(10)
        font_layout.addWidget(QLabel("Detail:"))
        self.stack_bar_font_size_spinbox = QSpinBox()
        self.stack_bar_font_size_spinbox.setRange(1, 50)
        self.stack_bar_font_size_spinbox.setValue(9)
        self.stack_bar_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.stack_bar_font_size_spinbox)

        font_layout.addWidget(QLabel("Grid:"))
        self.grid_label_font_size_spinbox = QSpinBox()
        self.grid_label_font_size_spinbox.setRange(1, 50)
        self.grid_label_font_size_spinbox.setValue(8)
        self.grid_label_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.grid_label_font_size_spinbox)

        font_layout.addWidget(QLabel("Title:"))
        self.title_font_size_spinbox = QSpinBox()
        self.title_font_size_spinbox.setRange(1, 50)
        self.title_font_size_spinbox.setValue(12)
        self.title_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.title_font_size_spinbox)

        font_layout.addWidget(QLabel("Level:"))
        self.borehole_level_font_size_spinbox = QSpinBox()
        self.borehole_level_font_size_spinbox.setRange(1, 50)
        self.borehole_level_font_size_spinbox.setValue(10)
        self.borehole_level_font_size_spinbox.setMaximumWidth(80)
        font_layout.addWidget(self.borehole_level_font_size_spinbox)

        font_group.setLayout(font_layout)
        plot_settings_layout.addWidget(font_group)

        # Horizontal line
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line3)

        # Profile Dimensions
        dim_group = QGroupBox("Profile Dimensions")
        dim_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        dim_layout = QHBoxLayout()
        dim_layout.setSpacing(10)
        dim_layout.addWidget(QLabel("Profile Width (m):"))
        self.plot_width = QSpinBox()
        self.plot_width.setRange(1, 100)
        self.plot_width.setValue(2)
        dim_layout.addWidget(self.plot_width)
        dim_layout.addWidget(QLabel("Borehole Spacing (m):"))
        self.plot_gap = QSpinBox()
        self.plot_gap.setRange(0, 100)
        self.plot_gap.setValue(15)
        dim_layout.addWidget(self.plot_gap)
        dim_group.setLayout(dim_layout)
        plot_settings_layout.addWidget(dim_group)

        # Scaled PDF Export
        pdf_group = QGroupBox("Scaled PDF Export")
        pdf_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        pdf_layout = QHBoxLayout()

        pdf_layout.addWidget(QLabel("Paper:"))
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(["A0","A1","A3","A4","Letter"])
        pdf_layout.addWidget(self.paper_combo)

        pdf_layout.addWidget(QLabel("Orientation:"))
        self.orient_combo = QComboBox()
        self.orient_combo.addItems(["Portrait","Landscape"])
        pdf_layout.addWidget(self.orient_combo)

        pdf_layout.addWidget(QLabel("Scale:"))
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(self.SCALE_OPTIONS)
        pdf_layout.addWidget(self.scale_combo)

        save_pdf_btn = QPushButton("Save PDF (Scaled)")
        save_pdf_btn.clicked.connect(self.save_pdf_scaled)
        pdf_layout.addWidget(save_pdf_btn)

        pdf_group.setLayout(pdf_layout)
        plot_settings_layout.addWidget(pdf_group)

        plot_settings_group.setLayout(plot_settings_layout)
        right_layout.addWidget(plot_settings_group)

        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 1000])
        self.setCentralWidget(main_splitter)

    def import_csv(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
            if not filename:
                return
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    table = self.bh1_table if row['Borehole'] == '1' else self.bh2_table
                    layer_no = int(row['Layer No']) - 1
                    while table.rowCount() <= layer_no:
                        table.insertRow(table.rowCount())
                    table.setItem(layer_no, 0, QTableWidgetItem(row['Layer Name']))
                    table.setItem(layer_no, 1, QTableWidgetItem(row['Start Level (m)']))
                    table.setItem(layer_no, 2, QTableWidgetItem(row['End Level (m)']))
                    table.setItem(layer_no, 3, QTableWidgetItem(row['SPT Value']))
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"CSV Error: {str(e)}")

    def generate_plot(self):
        try:
            self.figure.clear()
            bh1_data = self.get_borehole_data(self.bh1_table)
            bh2_data = self.get_borehole_data(self.bh2_table)
            plot_width = self.plot_width.value()
            plot_gap = self.plot_gap.value()
            width_ratios = [1, 1]
            wspace = plot_gap / plot_width
            gs = self.figure.add_gridspec(1, 2, width_ratios=width_ratios, wspace=wspace)
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])

            # Compute global y-range from both boreholes.
            all_values = []
            for d in bh1_data + bh2_data:
                all_values.append(d['start'])
                all_values.append(d['end'])
            if all_values:
                global_y_max = max(all_values)
                global_y_min = min(all_values)
            else:
                global_y_max, global_y_min = 1, 0

            # Compute colors based on combined data (sort by top).
            combined_data = bh1_data + bh2_data
            if combined_data:
                unique_layers = {d['layer'] for d in combined_data}
                layer_tops = {
                    name: max(d['start'] for d in combined_data if d['layer'] == name)
                    for name in unique_layers
                }
                sorted_layers = sorted(unique_layers, key=lambda name: layer_tops[name], reverse=True)
                colors = self.get_colors(sorted_layers)
            else:
                colors = {}

            # Plot each borehole's profile.
            if bh1_data:
                self.plot_profile(ax1, bh1_data, self.bh1_name.text(), colors, plot_width, label_side="left")
            else:
                ax1.set_visible(False)
            if bh2_data:
                self.plot_profile(ax2, bh2_data, self.bh2_name.text(), colors, plot_width, label_side="right")
            else:
                ax2.set_visible(False)

            # Set both axes to the global y-range.
            for ax in (ax1, ax2):
                if ax.get_visible():
                    ax.set_ylim(global_y_min, global_y_max)
                    ax.patch.set_visible(False)
                    for spine in ax.spines.values():
                        spine.set_visible(False)
                    ax.tick_params(axis='both', which='both', length=0)

            # Set discrete y-ticks for each borehole from its own data, with 3 decimals.
            if bh1_data and ax1.get_visible():
                discrete_bh1 = sorted({d['start'] for d in bh1_data} | {d['end'] for d in bh1_data}, reverse=True)
                ax1.set_yticks(discrete_bh1)
                ax1.yaxis.tick_right()
                ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
                ax1.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())
            if bh2_data and ax2.get_visible():
                discrete_bh2 = sorted({d['start'] for d in bh2_data} | {d['end'] for d in bh2_data}, reverse=True)
                ax2.set_yticks(discrete_bh2)
                ax2.yaxis.tick_left()
                ax2.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
                ax2.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())

            # Turn off built-in grids
            for ax in (ax1, ax2):
                if ax.get_visible():
                    ax.xaxis.grid(False)
                    ax.yaxis.grid(False)

            # Draw horizontal grid lines if enabled.
            if self.grid_checkbox.isChecked():
                pos1 = ax1.get_position()
                pos2 = ax2.get_position()
                gap_x0 = pos1.x1
                gap_x1 = pos2.x0
                grid_interval = self.grid_interval_spinbox.value()
                grid_values = np.arange(global_y_max, global_y_min - grid_interval / 2, -grid_interval)
                grid_color = 'gray'
                for y in grid_values:
                    fig_y = ax1.transData.transform((0, y))[1] / self.figure.bbox.height
                    line = plt.Line2D(
                        [gap_x0, gap_x1], [fig_y, fig_y],
                        transform=self.figure.transFigure,
                        color=grid_color, linestyle=(0, (3, 3)), linewidth=0.5
                    )
                    self.figure.lines.append(line)
                    if self.grid_label_checkbox.isChecked():
                        x_center = (gap_x0 + gap_x1) / 2
                        data_offset = 0.05
                        offset_fig = (
                            ax1.transData.transform((0, y + data_offset))[1]
                            - ax1.transData.transform((0, y))[1]
                        ) / self.figure.bbox.height
                        label_y = fig_y + offset_fig
                        label_text = f"{y:.3f} mSHD"
                        self.figure.text(
                            x_center, label_y, label_text,
                            ha='center', va='bottom', color=grid_color,
                            fontsize=self.grid_label_font_size_spinbox.value()
                        )

            if ax1.get_visible():
                ax1.title.set_fontsize(self.title_font_size_spinbox.value())
            if ax2.get_visible():
                ax2.title.set_fontsize(self.title_font_size_spinbox.value())

            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def get_colors(self, layers):
        """
        Given a list of layer names, assign each a color from the selected palette.
        Colors cycle if more layers than available.
        If Halftone is enabled, lighten the palette.
        """
        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
        if self.halftone_checkbox.isChecked():
            palette = [convert_to_lighter(color) for color in palette]
        return {layer: palette[i % len(palette)] for i, layer in enumerate(layers)}

    def get_borehole_data(self, table):
        """
        Extract data from the given table.
         Each row must have:
           - 'layer': Layer Name
           - 'start': Start Level (m)
           - 'end': End Level (m)
           - 'spt': SPT Value (None if blank; otherwise int or text)
        Returns list sorted by start level (descending).
        """
        data = []
        for row in range(table.rowCount()):
            items = [table.item(row, col) for col in range(4)]
            if not items or items[0] is None:
                continue
            try:
                start_val = float(items[1].text())
                end_val   = float(items[2].text())
            except ValueError:
                # skip invalid numeric
                continue
            spt_text = items[3].text().strip() if items[3] is not None else ""
            try:
                spt_value = int(spt_text)
            except ValueError:
                spt_value = spt_text if spt_text else None
            layer_data = {
                'layer': items[0].text(),
                'start': start_val,
                'end':   end_val,
                'spt':   spt_value
            }
            data.append(layer_data)
        return sorted(data, key=lambda x: x['start'], reverse=True)

    def plot_profile(self, ax, data, borehole_name, colors, plot_width, label_side="left"):
        """
        Plot the soil profile on the provided axis.
        - Adds a custom background patch covering only the local data range
        - Each soil layer is a bar with black border
        - Labels are placed outside
        """
        if not data:
            ax.set_visible(False)
            return

        ax.set_title(borehole_name, pad=20)
        ax.title.set_fontsize(self.title_font_size_spinbox.value())
        ax.set_xticks([])
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-plot_width / 2, plot_width / 2)

        local_box_top = max(d['start'] for d in data)
        local_box_bottom = min(d['end'] for d in data)
        x_left, x_right = ax.get_xlim()

        # Outline rectangle
        rect = plt.Rectangle(
            (x_left, local_box_bottom),
            x_right - x_left,
            local_box_top - local_box_bottom,
            fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False
        )
        ax.add_patch(rect)

        margin = 0.2 * plot_width
        for layer in data:
            thickness = abs(layer['start'] - layer['end'])
            bottom_val = min(layer['start'], layer['end'])
            c = colors[layer['layer']]
            ax.bar(
                0, thickness,
                width=plot_width,
                bottom=bottom_val,
                color=c,
                edgecolor='black',
                linewidth=0.5,
                zorder=2
            )
            if label_side == "left":
                text_x = -plot_width / 2 - margin
                ha = "right"
            else:
                text_x = plot_width / 2 + margin
                ha = "left"
            spt_display = ""
            if layer['spt'] not in [None, ""]:
                spt_display = f"SPT: {layer['spt']}"
            label_text = layer['layer'] if not spt_display else f"{layer['layer']}\n{spt_display}"
            ax.text(
                text_x,
                bottom_val + thickness / 2,
                label_text,
                ha=ha,
                va='center',
                fontsize=self.stack_bar_font_size_spinbox.value(),
                zorder=3
            )

    ###########################################################################
    # New function: save_pdf_scaled
    ###########################################################################
    def save_pdf_scaled(self):
        """
        Creates a new figure for scaled PDF export.
        Matches logic from generate_plot but with scaling: '1:50' => factor=50 => 1m => 20mm, etc.
        """
        # Gather data from both BH tables
        bh1_data = self.get_borehole_data(self.bh1_table)
        bh2_data = self.get_borehole_data(self.bh2_table)
        combined = bh1_data + bh2_data
        if not combined:
            QMessageBox.warning(self, "No Data", "No borehole data found.")
            return

        # parse scale string, e.g. "1:50" => factor=50
        scale_str = self.scale_combo.currentText()
        try:
            scale_factor = float(scale_str.split(":")[1])
        except:
            scale_factor = 50.0

        # pick paper size in inches
        paper_key = self.paper_combo.currentText()
        paper_w_in, paper_h_in = PAPER_SIZES_INCHES.get(paper_key, (11.69, 16.54))
        if self.orient_combo.currentText().lower() == "landscape":
            paper_w_in, paper_h_in = paper_h_in, paper_w_in

        # create a new figure for the PDF
        fig = plt.figure(figsize=(paper_w_in, paper_h_in))
        # replicate logic from generate_plot
        wspace = self.plot_gap.value() / max(self.plot_width.value(), 1e-6)
        gs = fig.add_gridspec(1, 2, width_ratios=[1,1], wspace=wspace)
        ax1 = fig.add_subplot(gs[0])
        ax2 = fig.add_subplot(gs[1])

        # compute global y-range
        all_vals = []
        for d in combined:
            all_vals.append(d['start'])
            all_vals.append(d['end'])
        if all_vals:
            y_min = min(all_vals)
            y_max = max(all_vals)
        else:
            y_min, y_max = 0, 1

        # replicate color sorting logic
        unique_layers = {d['layer'] for d in combined}
        layer_tops = {}
        for d in combined:
            if d['layer'] not in layer_tops:
                layer_tops[d['layer']] = d['start']
            else:
                layer_tops[d['layer']] = max(layer_tops[d['layer']], d['start'])
        sorted_layers = sorted(unique_layers, key=lambda n: layer_tops[n], reverse=True)

        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
        if self.halftone_checkbox.isChecked():
            palette = [convert_to_lighter(c) for c in palette]
        color_map = {layer: palette[i % len(palette)] for i, layer in enumerate(sorted_layers)}

        def plot_borehole_scaled(ax, data, name, label_side="left"):
            if not data:
                ax.set_visible(False)
                return
            ax.set_title(name, pad=20, fontsize=self.title_font_size_spinbox.value())
            ax.set_xticks([])
            ax.set_aspect('equal', adjustable='box')

            # scaled X-limits => 1 m => (1000/scale_factor)
            scaled_w = (self.plot_width.value()*1000.0)/scale_factor
            ax.set_xlim(-scaled_w/2, scaled_w/2)

            local_top = max(d['start'] for d in data)
            local_bot = min(d['end'] for d in data)
            scaled_bot = (local_bot*1000.0)/scale_factor
            scaled_top = (local_top*1000.0)/scale_factor

            x_left, x_right = ax.get_xlim()
            rect = plt.Rectangle(
                (x_left, scaled_bot),
                x_right - x_left,
                scaled_top - scaled_bot,
                fill=False, edgecolor='black', linewidth=1,
                zorder=1, clip_on=False
            )
            ax.add_patch(rect)

            margin = 0.2*scaled_w
            for layer in data:
                c = color_map.get(layer['layer'], "#CCCCCC")
                thick_m = abs(layer['start'] - layer['end'])
                thick_scaled = thick_m * 1000.0 / scale_factor
                btm = min(layer['start'], layer['end'])
                scaled_btm = btm*1000.0 / scale_factor
                ax.bar(
                    0, thick_scaled,
                    width=scaled_w,
                    bottom=scaled_btm,
                    color=c, edgecolor='black', linewidth=0.5, zorder=2
                )
                if label_side=="left":
                    text_x = x_left - margin
                    ha = "right"
                else:
                    text_x = x_right + margin
                    ha = "left"
                spt_display = ""
                if layer['spt'] not in [None, ""]:
                    spt_display = f"SPT: {layer['spt']}"
                label_text = layer['layer'] if not spt_display else f"{layer['layer']}\n{spt_display}"
                ax.text(
                    text_x,
                    scaled_btm + thick_scaled/2,
                    label_text,
                    ha=ha, va='center',
                    fontsize=self.stack_bar_font_size_spinbox.value(),
                    zorder=3
                )

        # Plot BH1 & BH2
        bh1_data = [d for d in combined if d in self.get_borehole_data(self.bh1_table)]
        bh2_data = [d for d in combined if d in self.get_borehole_data(self.bh2_table)]
        plot_borehole_scaled(ax1, bh1_data, self.bh1_name.text(), "left")
        plot_borehole_scaled(ax2, bh2_data, self.bh2_name.text(), "right")

        bh1_specific = bh1_data
        bh2_specific = bh2_data
        

        # set scaled y-lims
        scaled_min = (y_min*1000.0)/scale_factor
        scaled_max = (y_max*1000.0)/scale_factor
        # 3) Loop over both axes
        for ax in (ax1, ax2):
            ax.set_ylim(scaled_min, scaled_max)
            for spine in ax.spines.values():
                spine.set_visible(False)
            # hide x ticks only
            ax.set_xticks([])
            ax.tick_params(axis='x', which='both', bottom=False, labelbottom=False)
            ax.tick_params(axis='both', which='both', length=0)

        # BH1 discrete ticks
        if bh1_specific and ax1.get_visible():
            discrete_scaled = []
            for d in bh1_specific:
                discrete_scaled.append((d["start"]*1000.0)/scale_factor)
                discrete_scaled.append((d["end"]  *1000.0)/scale_factor)
            discrete_scaled = sorted(set(discrete_scaled), reverse=True)
            ax1.set_yticks(discrete_scaled)
            def format_meters(val, pos):
                real_m = (val*scale_factor)/1000.0
                return f"{real_m:.3f}"
            ax1.yaxis.set_major_formatter(mticker.FuncFormatter(format_meters))
            ax1.yaxis.tick_right()
            ax1.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())

        # BH2 discrete ticks
        if bh2_specific and ax2.get_visible():
            discrete_scaled = []
            for d in bh2_specific:
                discrete_scaled.append((d["start"]*1000.0)/scale_factor)
                discrete_scaled.append((d["end"]  *1000.0)/scale_factor)
            discrete_scaled = sorted(set(discrete_scaled), reverse=True)
            ax2.set_yticks(discrete_scaled)
            def format_meters(val, pos):
                real_m = (val*scale_factor)/1000.0
                return f"{real_m:.3f}"
            ax2.yaxis.set_major_formatter(mticker.FuncFormatter(format_meters))
            ax2.yaxis.tick_left()
            ax2.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())



        # optional horizontal lines if user wants them
        if self.grid_checkbox.isChecked() and ax1.get_visible() and ax2.get_visible():
            pos1 = ax1.get_position()
            pos2 = ax2.get_position()
            gap_x0 = pos1.x1
            gap_x1 = pos2.x0
            interval_m = self.grid_interval_spinbox.value()
            scaled_interval = (interval_m * 1000.0) / scale_factor
            scaled_vals = np.arange(scaled_max, scaled_min - scaled_interval/2, -scaled_interval)
            grid_color = 'gray'
            for yv in scaled_vals:
                fig_y = ax1.transData.transform((0,yv))[1] / fig.bbox.height
                line = plt.Line2D([gap_x0, gap_x1], [fig_y, fig_y],
                                  transform=fig.transFigure,
                                  color=grid_color, linestyle=(0,(3,3)), linewidth=0.5)
                fig.lines.append(line)
                if self.grid_label_checkbox.isChecked():
                    x_center = (gap_x0 + gap_x1)/2
                    offset_val = (0.05*1000.0)/scale_factor
                    off_fig = (
                        ax1.transData.transform((0, yv+offset_val))[1]
                        - ax1.transData.transform((0, yv))[1]
                    ) / fig.bbox.height
                    label_y = fig_y + off_fig
                    # convert scaled y => real meters
                    real_m = (yv * scale_factor)/1000.0
                    label_text = f"{real_m:.3f} m"
                    fig.text(
                        x_center, label_y, label_text,
                        ha='center', va='bottom', color=grid_color,
                        fontsize=self.grid_label_font_size_spinbox.value()
                    )

        # prompt user for pdf filename
        out_file, _ = QFileDialog.getSaveFileName(self, "Save PDF (Scaled)", "", "PDF Files (*.pdf)")
        if not out_file:
            plt.close(fig)
            return

        try:
            fig.savefig(out_file, format="pdf", dpi=300)
            QMessageBox.information(self, "Saved PDF", f"Saved scaled PDF to: {out_file}")
        except Exception as ee:
            QMessageBox.warning(self, "Save PDF Error", f"Could not save PDF: {str(ee)}")
        finally:
            plt.close(fig)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
