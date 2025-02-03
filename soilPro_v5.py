import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QLineEdit,
    QFileDialog, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt


class EnhancedTable(QTableWidget):
    """
    Custom QTableWidget with enhanced features:
      - Predefined headers and column widths.
      - Right-click context menu for copying, pasting, and clearing cells.
    """
    HEADER_HEIGHT = 60
    COLUMN_WIDTHS = [120, 100, 100, 80]
    COLUMN_PADDING = 15

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
        # Set each column width (with extra padding).
        for col, width in enumerate(self.COLUMN_WIDTHS):
            self.setColumnWidth(col, width + self.COLUMN_PADDING)
        header.setStyleSheet("""
            QHeaderView::section {
                border: 1px solid #ddd;
                padding: 4px;
                font-weight: bold;
            }
        """)

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
    Contains:
      - Input fields for borehole names, color palette, and gridlines toggle.
      - Two tables for borehole data input.
      - Buttons to import CSV data and generate plots.
      - A matplotlib canvas for displaying soil profile plots.
    """
    COLOR_PALETTES = {
        "Geotech 12": [
            '#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6',
            '#4292c6', '#2171b5', '#08519c', '#08306b', '#082252',
            '#081538', '#080c1e'
        ],
        "Earth Tones": [
            '#fff7bc', '#fee391', '#fec44f', '#fe9929', '#ec7014',
            '#cc4c02', '#993404', '#662506', '#4d1c02', '#331302',
            '#1a0a01', '#000000'
        ]
    }

    def __init__(self):
        super().__init__()
        self.init_ui()  # Set up the user interface.
        self.setWindowTitle("Geotechnical Profile Analyzer")
        self.setGeometry(100, 100, 1400, 900)

    def init_ui(self):
        """Initialize and arrange all UI components."""
        main_splitter = QSplitter(Qt.Horizontal)
        # Left Panel: Contains controls and data tables.
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        self.bh1_name = QLineEdit("Borehole-1")
        self.bh2_name = QLineEdit("Borehole-2")
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        self.plot_width = QSpinBox()
        self.plot_width.setRange(1, 100)
        self.plot_width.setValue(2)
        self.plot_gap = QSpinBox()
        self.plot_gap.setRange(0, 100)
        self.plot_gap.setValue(15)
        self.grid_checkbox = QCheckBox("Show Horizontal Gridlines")
        self.grid_checkbox.setChecked(True)
        layout.addWidget(QLabel("Borehole Names:"))
        layout.addWidget(self.bh1_name)
        layout.addWidget(self.bh2_name)
        layout.addWidget(QLabel("Color Palette:"))
        layout.addWidget(self.palette_selector)
        layout.addWidget(QPushButton("Import CSV", clicked=self.import_csv))
        layout.addWidget(self.grid_checkbox)
        layout.addWidget(QLabel("Borehole 1 Data:"))
        self.bh1_table = EnhancedTable()
        layout.addWidget(self.bh1_table)
        layout.addWidget(QLabel("Borehole 2 Data:"))
        self.bh2_table = EnhancedTable()
        layout.addWidget(self.bh2_table)
        controls = QGridLayout()
        controls.addWidget(QLabel("Profile Width (m):"), 0, 0)
        controls.addWidget(self.plot_width, 0, 1)
        controls.addWidget(QLabel("Borehole Spacing (m):"), 1, 0)
        controls.addWidget(self.plot_gap, 1, 1)
        layout.addLayout(controls)
        layout.addWidget(QPushButton("Generate Profile", clicked=self.generate_plot))
        # Right Panel: Contains the matplotlib canvas and toolbar.
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 1000])
        self.setCentralWidget(main_splitter)

    def import_csv(self):
        """
        Open a CSV file and populate the appropriate borehole table.
        Expected CSV columns: Borehole,Layer No,Layer Name,Start Level (m),End Level (m),SPT Value
        """
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
        """
        Generate the soil profile plots.
         - Compute a global y-range from all values for alignment.
         - Set each axis to this global range.
         - Remove all borders and ticks except for the discrete y values from each borehole's data.
         - For each borehole, compute its own discrete y-values and set them on the corresponding axis.
         - The axis for Borehole 1 shows y-values on the right; for Borehole 2 on the left.
         - The stack bar (soil profile box) is drawn with a full border.
        """
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
            
            # Compute global y-range from both boreholes
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

            # Plot profiles for each borehole if data exists.
            if bh1_data:
                self.plot_profile(ax1, bh1_data, self.bh1_name.text(), colors, plot_width, label_side="left")
            else:
                ax1.set_visible(False)
            if bh2_data:
                self.plot_profile(ax2, bh2_data, self.bh2_name.text(), colors, plot_width, label_side="right")
            else:
                ax2.set_visible(False)
            
            # Set both axes to the global y-range.
            if ax1.get_visible():
                ax1.set_ylim(global_y_min, global_y_max)
            if ax2.get_visible():
                ax2.set_ylim(global_y_min, global_y_max)
            
            # Remove all axis borders and ticks.
            for ax in (ax1, ax2):
                if ax.get_visible():
                    ax.patch.set_visible(False)
                    for spine in ax.spines.values():
                        spine.set_visible(False)
                    ax.tick_params(axis='both', which='both', length=0)
            
            # Set discrete y-ticks from each borehole's own data.
            if bh1_data and ax1.get_visible():
                discrete_bh1 = sorted(set([d['start'] for d in bh1_data] + [d['end'] for d in bh1_data]), reverse=True)
                ax1.set_yticks(discrete_bh1)
                ax1.yaxis.tick_right()  # Show Borehole 1 y-values on the right.
            if bh2_data and ax2.get_visible():
                discrete_bh2 = sorted(set([d['start'] for d in bh2_data] + [d['end'] for d in bh2_data]), reverse=True)
                ax2.set_yticks(discrete_bh2)
                ax2.yaxis.tick_left()   # Show Borehole 2 y-values on the left.
            
            # Remove grid lines.
            for ax in (ax1, ax2):
                if ax.get_visible():
                    ax.xaxis.grid(False)
                    ax.yaxis.grid(False)
            
            self.canvas.draw()
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def get_colors(self, layers):
        """
        Given a list of layer names, assign each a color from the selected palette.
        Colors cycle if there are more layers than available.
        """
        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
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
         - Adds a custom background patch covering only the borehole's local data range.
         - Draws each soil layer as a bar with a black border.
         - Places the label (with optional SPT info) outside the bar.
         - The background patch (stack bar box) is drawn with a full border on all sides.
        """
        if not data:
            ax.set_visible(False)
            return
        
        ax.set_title(borehole_name, pad=20)
        ax.set_xticks([])
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-plot_width / 2, plot_width / 2)
        
        # Compute local data range for this borehole.
        local_box_top = max(d['start'] for d in data)
        local_box_bottom = min(d['end'] for d in data)
        
        # Add a custom background patch covering only the local data range.
        x_left, x_right = ax.get_xlim()
        # Use fill=False and clip_on=False to ensure all borders are drawn.
        rect = plt.Rectangle((x_left, local_box_bottom),
                             x_right - x_left,
                             local_box_top - local_box_bottom,
                             fill=False, edgecolor='black', linewidth=1, zorder=1, clip_on=False)
        ax.add_patch(rect)
        
        # Draw each soil layer as a bar.
        margin = 0.2 * plot_width  # Margin for label placement.
        for layer in data:
            thickness = abs(layer['start'] - layer['end'])
            bottom_val = min(layer['start'], layer['end'])
            ax.bar(0, thickness, width=plot_width,
                   bottom=bottom_val,
                   color=colors[layer['layer']],
                   edgecolor='black',
                   linewidth=0.5,
                   zorder=2)
            # Determine label position.
            if label_side == "left":
                ha = "right"
                text_x = -plot_width / 2 - margin
            else:
                ha = "left"
                text_x = plot_width / 2 + margin
            # Build label text.
            if layer['spt'] is None or layer['spt'] == "":
                spt_display = ""
            else:
                spt_display = f"SPT: {layer['spt']}"
            label_text = layer['layer'] if spt_display == "" else f"{layer['layer']}\n{spt_display}"
            ax.text(text_x, bottom_val + thickness / 2,
                    label_text, ha=ha, va='center', fontsize=9, zorder=3)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
