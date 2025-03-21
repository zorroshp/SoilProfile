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
from PyQt5.QtGui import QClipboard, QIcon
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt


def convert_to_lighter(hex_color, factor=0.5):
    """
    Convert a hex color (e.g. '#RRGGBB') to a lighter version by blending with white.
    The blending factor determines how much lighter the color should be.
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
        # Initialize with 15 rows and 4 columns.
        super().__init__(15, 4)
        self.setup_table()  # Set up headers and column widths.
        self.clipboard = QApplication.clipboard()  # Access system clipboard.
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
        self.verticalHeader().setDefaultSectionSize(10)  # Change 30 to your desired row height in pixels.


    def context_menu(self, position):
        """
        Display a custom context menu with options:
          - Copy: Copies selected cells to clipboard.
          - Paste: Pastes clipboard content into selected cells.
          - Clear: Clears the text in selected cells.
        """
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
        """Copy the selected cell(s) content to the clipboard."""
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
        """Paste clipboard text into the table starting at the current cell."""
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
        """Clear the text of all selected cells."""
        for item in self.selectedItems():
            item.setText("")

    def keyPressEvent(self, event):
        """Override Delete key press to clear selection."""
        if event.key() == Qt.Key_Delete:
            self.clear_selection()
        else:
            super().keyPressEvent(event)


class SoilProfileApp(QMainWindow):
    """
    Main application window for the Geotechnical Profile Analyzer.
    The functionality remains unchanged, but the GUI layout has been reorganized
    into modern, user-friendly groupings. The window title is set to "SoilPro" with an icon.
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

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowTitle("SoilPro")
        self.setWindowIcon(QIcon("soilpro_icon.png"))
        self.setGeometry(50, 50, 1600, 950)


    def init_ui(self):
        """Set up a modern, user-friendly GUI layout."""
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel Setup
        left_panel = QWidget()
        left_panel.setMinimumWidth(480)  # Minimum width of 300 pixels.
        left_panel.setMaximumWidth(485)  # Maximum width of 500 pixels.

        left_layout = QVBoxLayout(left_panel)
        
        # Borehole Information Section
        borehole_group = QGroupBox("Borehole Information")
        borehole_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = borehole_group.font()
        font.setBold(True)
        borehole_group.setFont(font)
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
        
        # Plot Settings Section
        plot_settings_group = QGroupBox("Plot Settings")
        plot_settings_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = plot_settings_group.font()
        font.setBold(True)
        plot_settings_group.setFont(font)
        plot_settings_layout = QVBoxLayout()
        
        # Section: Color Palette
        cp_group = QGroupBox("Color Palette")
        cp_layout = QHBoxLayout()
        cp_layout.setSpacing(10)  # Adjust 10 to your desired pixel gap
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        self.halftone_checkbox = QCheckBox("Halftone")
        self.halftone_checkbox.setChecked(False)
        cp_layout.addWidget(QLabel("Select Palette:"))
        cp_layout.addWidget(self.palette_selector)
        cp_layout.addWidget(self.halftone_checkbox)
        cp_group.setLayout(cp_layout)
        plot_settings_layout.addWidget(cp_group)
        
        # Add horizontal line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line1)
        
        # Section: Grid Settings
        grid_group = QGroupBox("Grid Settings")
        grid_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = grid_group.font()
        font.setBold(True)
        grid_group.setFont(font)
        grid_layout = QHBoxLayout()
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
        #grid_group.setContentsMargins(5, 5, 5, 5)
        plot_settings_layout.addWidget(grid_group)

        
        # Add horizontal line
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line2)
        
        # Section: Font Sizes
        font_group = QGroupBox("Font Sizes")
        font_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = font_group.font()
        font.setBold(True)
        font_group.setFont(font)
        font_layout = QHBoxLayout()
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
        
        # Add horizontal line
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        plot_settings_layout.addWidget(line3)
        
        # Section: Profile Dimensions
        dim_group = QGroupBox("Profile Dimensions")
        dim_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = dim_group.font()
        font.setBold(True)
        dim_group.setFont(font)
        dim_layout = QHBoxLayout()
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
        
        plot_settings_group.setLayout(plot_settings_layout)
        left_layout.addWidget(plot_settings_group)
        
        # Borehole Data Section (both boreholes shown vertically)
        data_group = QGroupBox("Borehole Data")
        data_group.setStyleSheet("QGroupBox::title { font: bold 8pt; }")
        font = data_group.font()
        font.setBold(True)
        data_group.setFont(font)
        data_layout = QVBoxLayout()
        data_layout.addWidget(QLabel("Borehole 1 Data:"))
        self.bh1_table = EnhancedTable()
        data_layout.addWidget(self.bh1_table)
        data_layout.addWidget(QLabel("Borehole 2 Data:"))
        self.bh2_table = EnhancedTable()
        data_layout.addWidget(self.bh2_table)
        data_group.setLayout(data_layout)
        left_layout.addWidget(data_group)
        
        # Generate Profile Button
        left_layout.addWidget(QPushButton("Generate Profile", clicked=self.generate_plot))
        
        # Right Panel: Plot Area remains unchanged.
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)
        
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

            # Compute colors based on combined data.
            combined_data = bh1_data + bh2_data
            if combined_data:
                unique_layers = {d['layer'] for d in combined_data}
                layer_tops = {name: max(d['start'] for d in combined_data if d['layer'] == name)
                              for name in unique_layers}
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
                discrete_bh1 = sorted(set([d['start'] for d in bh1_data] + [d['end'] for d in bh1_data]), reverse=True)
                ax1.set_yticks(discrete_bh1)
                ax1.yaxis.tick_right()
                ax1.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
                ax1.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())
            if bh2_data and ax2.get_visible():
                discrete_bh2 = sorted(set([d['start'] for d in bh2_data] + [d['end'] for d in bh2_data]), reverse=True)
                ax2.set_yticks(discrete_bh2)
                ax2.yaxis.tick_left()
                ax2.yaxis.set_major_formatter(plt.FormatStrFormatter('%.3f'))
                ax2.tick_params(axis='y', labelsize=self.borehole_level_font_size_spinbox.value())
            
            # Borehole plot borders remain unchanged.
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
                grid_values = np.arange(global_y_max, global_y_min - grid_interval/2, -grid_interval)
                grid_color = 'gray'
                for y in grid_values:
                    fig_y = ax1.transData.transform((0, y))[1] / self.figure.bbox.height
                    line = plt.Line2D([gap_x0, gap_x1], [fig_y, fig_y],
                                      transform=self.figure.transFigure,
                                      color=grid_color, linestyle=(0, (3, 3)), linewidth=0.5)
                    self.figure.lines.append(line)
                    if self.grid_label_checkbox.isChecked():
                        x_center = (gap_x0 + gap_x1) / 2
                        data_offset = 0.05
                        offset_fig = (ax1.transData.transform((0, y + data_offset))[1] -
                                      ax1.transData.transform((0, y))[1]) / self.figure.bbox.height
                        label_y = fig_y + offset_fig
                        label_text = f"{y:.3f} mSHD"
                        self.figure.text(x_center, label_y, label_text,
                                         ha='center', va='bottom', color=grid_color,
                                         fontsize=self.grid_label_font_size_spinbox.value())
            
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
        Colors cycle if there are more layers than available.
        If the Halftone option is enabled, convert each color to a lighter version.
        """
        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
        if self.halftone_checkbox.isChecked():
            palette = [convert_to_lighter(color) for color in palette]
        return {layer: palette[i % len(palette)] for i, layer in enumerate(layers)}

    def get_borehole_data(self, table):
        """
        Extract data from the given table.
         Each row must have:
           - 'layer': Layer Name (string)
           - 'start': Start Level (m) (float)
           - 'end': End Level (m) (float)
           - 'spt': SPT Value (None if blank; otherwise int or text)
         Returns a list sorted by start level (descending).
        """
        data = []
        for row in range(table.rowCount()):
            items = [table.item(row, col) for col in range(4)]
            if not items or items[0] is None:
                continue
            try:
                start_val = float(items[1].text())
                end_val = float(items[2].text())
            except ValueError:
                continue
            spt_text = items[3].text().strip() if items[3] is not None else ""
            try:
                spt_value = int(spt_text)
            except ValueError:
                spt_value = spt_text if spt_text != "" else None
            layer_data = {
                'layer': items[0].text(),
                'start': start_val,
                'end': end_val,
                'spt': spt_value
            }
            data.append(layer_data)
        return sorted(data, key=lambda x: x['start'], reverse=True)

    def plot_profile(self, ax, data, borehole_name, colors, plot_width, label_side="left"):
        """
        Plot the soil profile on the provided axis.
         - Adds a custom background patch (the stack bar box) covering only the borehole's local data range,
           drawn with full borders on all sides.
         - Draws each soil layer as a bar with its own black border.
         - Places the label (with optional SPT info) outside the bar.
         - Borehole border settings remain exactly as in previous code.
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
        rect = plt.Rectangle((x_left, local_box_bottom),
                             x_right - x_left,
                             local_box_top - local_box_bottom,
                             fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False)
        ax.add_patch(rect)
        
        margin = 0.2 * plot_width
        for layer in data:
            thickness = abs(layer['start'] - layer['end'])
            bottom_val = min(layer['start'], layer['end'])
            ax.bar(0, thickness, width=plot_width,
                   bottom=bottom_val,
                   color=colors[layer['layer']],
                   edgecolor='black',
                   linewidth=0.5,
                   zorder=2)
            if label_side == "left":
                ha = "right"
                text_x = -plot_width / 2 - margin
            else:
                ha = "left"
                text_x = plot_width / 2 + margin
            if layer['spt'] is None or layer['spt'] == "":
                spt_display = ""
            else:
                spt_display = f"SPT: {layer['spt']}"
            label_text = layer['layer'] if spt_display == "" else f"{layer['layer']}\n{spt_display}"
            ax.text(text_x, bottom_val + thickness / 2,
                    label_text, ha=ha, va='center',
                    fontsize=self.stack_bar_font_size_spinbox.value(), zorder=3)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
