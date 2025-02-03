import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QLineEdit,
    QFileDialog, QComboBox
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
        self.setup_table()  # Set up table headers and column widths.
        self.clipboard = QApplication.clipboard()  # Access system clipboard.
        # Enable custom context menu on right-click.
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def setup_table(self):
        """Set up the table with headers and predefined column widths."""
        headers = ["Layer\nName", "Start\nLevel (m)", "End\nLevel (m)", "SPT\nValue"]
        self.setHorizontalHeaderLabels(headers)
        
        header = self.horizontalHeader()
        header.setFixedHeight(self.HEADER_HEIGHT)
        header.setDefaultAlignment(Qt.AlignCenter)
        
        # Set each column width including extra padding.
        for col, width in enumerate(self.COLUMN_WIDTHS):
            self.setColumnWidth(col, width + self.COLUMN_PADDING)
        
        # Apply CSS style to header sections.
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
        """Copy the currently selected cell(s) content to the clipboard."""
        selected = self.selectedRanges()
        if not selected:
            return
        
        text = ""
        # Loop through each selected range and each cell within the range.
        for range in selected:
            for row in range(range.topRow(), range.bottomRow() + 1):
                for col in range(range.leftColumn(), range.rightColumn() + 1):
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
                # Only paste if within table boundaries.
                if row_pos < self.rowCount() and col_pos < self.columnCount():
                    self.setItem(row_pos, col_pos, QTableWidgetItem(cell.strip()))

    def clear_selection(self):
        """Clear the text of all selected cells."""
        for item in self.selectedItems():
            item.setText("")

    def keyPressEvent(self, event):
        """Override key press event to clear selection on Delete key."""
        if event.key() == Qt.Key_Delete:
            self.clear_selection()
        else:
            super().keyPressEvent(event)


class SoilProfileApp(QMainWindow):
    """
    Main application window for the Geotechnical Profile Analyzer.
    Includes:
      - Input fields for borehole names and color palette.
      - Two tables for borehole data input.
      - Buttons to import CSV data and generate plots.
      - A matplotlib canvas for displaying the soil profile plots.
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
        """Initialize and layout all UI components."""
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Controls and data tables.
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        # Input fields for borehole names.
        self.bh1_name = QLineEdit("Borehole-1")
        self.bh2_name = QLineEdit("Borehole-2")
        
        # Dropdown for selecting color palette.
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        
        # SpinBoxes for adjusting plot width and borehole spacing.
        self.plot_width = QSpinBox()
        self.plot_width.setRange(1, 100)
        self.plot_width.setValue(2)
        self.plot_gap = QSpinBox()
        self.plot_gap.setRange(0, 100)
        self.plot_gap.setValue(15)
        
        # Organize controls in the left panel.
        layout.addWidget(QLabel("Borehole Names:"))
        layout.addWidget(self.bh1_name)
        layout.addWidget(self.bh2_name)
        layout.addWidget(QLabel("Color Palette:"))
        layout.addWidget(self.palette_selector)
        layout.addWidget(QPushButton("Import CSV", clicked=self.import_csv))
        
        # Tables for Borehole 1 and Borehole 2 data.
        layout.addWidget(QLabel("Borehole 1 Data:"))
        self.bh1_table = EnhancedTable()
        layout.addWidget(self.bh1_table)
        layout.addWidget(QLabel("Borehole 2 Data:"))
        self.bh2_table = EnhancedTable()
        layout.addWidget(self.bh2_table)
        
        # Layout for plot control parameters.
        controls = QGridLayout()
        controls.addWidget(QLabel("Profile Width (m):"), 0, 0)
        controls.addWidget(self.plot_width, 0, 1)
        controls.addWidget(QLabel("Borehole Spacing (m):"), 1, 0)
        controls.addWidget(self.plot_gap, 1, 1)
        layout.addLayout(controls)
        layout.addWidget(QPushButton("Generate Profile", clicked=self.generate_plot))

        # Right Panel: Matplotlib plot and toolbar.
        self.figure = plt.figure(figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(toolbar)
        right_layout.addWidget(self.canvas)

        # Combine left and right panels.
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([400, 1000])
        
        self.setCentralWidget(main_splitter)

    def import_csv(self):
        """
        Open a CSV file and populate the appropriate borehole table.
        The CSV should include columns:
          - Borehole (value "1" or "2")
          - Layer No
          - Layer Name
          - Start Level (m)
          - End Level (m)
          - SPT Value
        """
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
            if not filename:
                return
            
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Select the appropriate table based on the Borehole column.
                    table = self.bh1_table if row['Borehole'] == '1' else self.bh2_table
                    layer_no = int(row['Layer No']) - 1
                    
                    # Ensure the table has enough rows.
                    while table.rowCount() <= layer_no:
                        table.insertRow(table.rowCount())
                    
                    # Populate table cells with CSV data.
                    table.setItem(layer_no, 0, QTableWidgetItem(row['Layer Name']))
                    table.setItem(layer_no, 1, QTableWidgetItem(row['Start Level (m)']))
                    table.setItem(layer_no, 2, QTableWidgetItem(row['End Level (m)']))
                    table.setItem(layer_no, 3, QTableWidgetItem(row['SPT Value']))
                    
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"CSV Error: {str(e)}")

    def generate_plot(self):
        """
        Generate the soil profile plot for both boreholes.
        - Reads data from the tables.
        - Calculates grid parameters based on user input.
        - Uses matplotlib to draw the profile bars and labels.
        """
        try:
            self.figure.clear()
            
            # Get borehole data from the respective tables.
            bh1_data = self.get_borehole_data(self.bh1_table)
            bh2_data = self.get_borehole_data(self.bh2_table)
            plot_width = self.plot_width.value()
            plot_gap = self.plot_gap.value()
            
            # Calculate grid spacing for side-by-side plots.
            width_ratios = [1, 1]
            wspace = plot_gap / plot_width
            
            # Create subplots for each borehole.
            gs = self.figure.add_gridspec(1, 2, width_ratios=width_ratios, wspace=wspace)
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])
            
            # Combine both borehole data to assign unique colors for each soil layer.
            combined_data = bh1_data + bh2_data
            unique_layers = {layer['layer'] for layer in combined_data}
            layer_tops = {
                name: max(layer['start'] for layer in combined_data if layer['layer'] == name)
                for name in unique_layers
            }
            sorted_layers = sorted(unique_layers, key=lambda name: layer_tops[name], reverse=True)
            colors = self.get_colors(sorted_layers)
            
            # Plot profiles: left panel for Borehole 1, right panel for Borehole 2.
            self.plot_profile(ax1, bh1_data, self.bh1_name.text(), colors, plot_width, label_side="left")
            self.plot_profile(ax2, bh2_data, self.bh2_name.text(), colors, plot_width, label_side="right")
            
            self.canvas.draw()  # Render the plot on the canvas.
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def get_colors(self, layers):
        """
        Given a list of layer names, assign each a color from the selected palette.
        Colors cycle through the palette if there are more layers than colors.
        """
        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
        return {layer: palette[i % len(palette)] for i, layer in enumerate(layers)}

    def get_borehole_data(self, table):
        """
        Extract and process data from a given table.
        Each row should have:
          - Layer name (string)
          - Start Level (float)
          - End Level (float)
          - SPT value (optional; if blank, remains None)
        Returns a sorted list (by start level) of dictionaries.
        """
        data = []
        for row in range(table.rowCount()):
            items = [table.item(row, col) for col in range(4)]
            if not items or items[0] is None:
                continue

            # Ensure necessary cells (Layer name, start, and end levels) exist.
            if items[0] is None or items[1] is None or items[2] is None:
                continue

            try:
                start_val = float(items[1].text())
                end_val = float(items[2].text())
            except ValueError:
                continue

            # Process SPT value:
            # If blank, store as None; otherwise, try converting to an int,
            # if conversion fails, store the text value.
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
                
        # Sort the data by the start level in ascending order.
        return sorted(data, key=lambda x: x['start'])

    def plot_profile(self, ax, data, borehole_name, colors, plot_width, label_side="left"):
        """
        Plot the soil profile on a given axis.
        - Each layer is drawn as a bar.
        - The label (layer name and optionally SPT info) is positioned completely outside the bar:
            - For Borehole 1 (label_side="left"): to the left of the bar.
            - For Borehole 2 (label_side="right"): to the right of the bar.
        - If SPT is blank, no SPT text is shown.
        """
        if not data:
            return
        
        # Set the title using the borehole name entered by the user.
        ax.set_title(borehole_name, pad=20)
        ax.set_xticks([])  # Remove x-axis tick marks.
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Ensure the aspect ratio remains consistent.
        ax.set_aspect('equal', adjustable='box')
        ax.set_xlim(-plot_width / 2, plot_width / 2)
        
        # Define margin to position text completely outside the soil profile bar.
        margin = 0.2 * plot_width
        
        for layer in data:
            # Calculate thickness and determine the bottom position of the bar.
            thickness = abs(layer['end'] - layer['start'])
            bottom_val = min(layer['start'], layer['end'])
            # Draw the bar representing the soil layer.
            ax.bar(0, thickness, width=plot_width,
                   bottom=bottom_val,
                   color=colors[layer['layer']],
                   edgecolor='black',
                   linewidth=0.5)
            
            # Determine horizontal alignment and x-position for the label.
            if label_side == "left":
                ha = "right"
                text_x = -plot_width / 2 - margin
            else:
                ha = "left"
                text_x = plot_width / 2 + margin
            
            # Build label text: if SPT is provided, include it on a new line.
            if layer['spt'] is None or layer['spt'] == "":
                spt_display = ""
            else:
                spt_display = f"SPT: {layer['spt']}"
            
            label_text = layer['layer'] if spt_display == "" else f"{layer['layer']}\n{spt_display}"
            
            # Place the text label at the vertical center of the layer bar.
            ax.text(text_x, bottom_val + thickness / 2,
                    label_text,
                    ha=ha, va='center', fontsize=9)
        
        # Adjust y-axis limits to include all layers.
        y_min = min(min(layer['start'], layer['end']) for layer in data)
        y_max = max(max(layer['start'], layer['end']) for layer in data)
        ax.set_ylim(y_min, y_max)


if __name__ == "__main__":
    # Create the QApplication and launch the SoilProfileApp.
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
