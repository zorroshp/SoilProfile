import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QLineEdit,
    QFileDialog, QComboBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics, QClipboard
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np


class EnhancedTable(QTableWidget):
    HEADER_HEIGHT = 60
    COLUMN_WIDTHS = [120, 100, 100, 80]
    COLUMN_PADDING = 15

    def __init__(self, parent=None):
        super().__init__(15, 4)
        self.parent = parent
        self.init_table()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        
    def init_table(self):
        headers = ["Layer\nName", "Start\nLevel\n(m)", "End\nLevel\n(m)", "SPT\nValue"]
        self.setHorizontalHeaderLabels(headers)
        self.setup_headers()
        
    def setup_headers(self):
        header = self.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setFixedHeight(self.HEADER_HEIGHT)
        
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
        menu = QMenu()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        delete_action = menu.addAction("Clear")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        
        if action == copy_action:
            self.copy_clipboard()
        elif action == paste_action:
            self.paste_clipboard()
        elif action == delete_action:
            self.clearSelectedCells()

    def copy_clipboard(self):
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return
        text = ""
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.item(row, col)
                    text += item.text() + '\t' if item else '\t'
                text = text.rstrip('\t') + '\n'
        self.clipboard.setText(text.strip())

    def paste_clipboard(self):
        text = self.clipboard.text()
        rows = text.split('\n')
        current_row = self.currentRow()
        current_col = self.currentColumn()
        for r, row in enumerate(rows):
            if row.strip():
                cells = row.split('\t')
                for c, cell in enumerate(cells):
                    row_position = current_row + r
                    col_position = current_col + c
                    if row_position < self.rowCount() and col_position < self.columnCount():
                        self.setItem(row_position, col_position, QTableWidgetItem(cell))

    def clearSelectedCells(self):
        for item in self.selectedItems():
            item.setText("")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.clearSelectedCells()
        else:
            super().keyPressEvent(event)


class SoilProfileApp(QMainWindow):
    INPUT_WIDTH = 400
    PLOT_HEIGHT_RATIO = 2
    PLOT_WIDTH_RATIO = 3

    # 12-Color Palettes
    COLOR_PALETTES = {
        "Browns": ["#f6e0b5", "#e6c8a5", "#d6b095", "#c69885", "#b68075", "#a66865", "#965055", "#863845", "#762035", "#660825", "#560015", "#460005"],
        "Blues": ["#e6f7ff", "#cceeff", "#b3e6ff", "#99ddff", "#80d4ff", "#66ccff", "#4dc3ff", "#33bbff", "#1ab2ff", "#00aaff", "#0099e6", "#0088cc"],
        "Greens": ["#e6ffe6", "#ccffcc", "#b3ffb3", "#99ff99", "#80ff80", "#66ff66", "#4dff4d", "#33ff33", "#1aff1a", "#00ff00", "#00e600", "#00cc00"],
        "Reds": ["#ffe6e6", "#ffcccc", "#ffb3b3", "#ff9999", "#ff8080", "#ff6666", "#ff4d4d", "#ff3333", "#ff1a1a", "#ff0000", "#e60000", "#cc0000"],
        "Purples": ["#f2e6ff", "#e6ccff", "#d9b3ff", "#cc99ff", "#bf80ff", "#b366ff", "#a64dff", "#9933ff", "#8c1aff", "#8000ff", "#7300e6", "#6600cc"]
    }

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.setWindowTitle("Advanced Soil Profile Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        self.current_palette = "Browns"

    def init_ui(self):
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        # Borehole Names
        self.bh1_name = QLineEdit("Borehole 1")
        self.bh2_name = QLineEdit("Borehole 2")
        layout.addWidget(QLabel("Borehole Names:"))
        layout.addWidget(self.bh1_name)
        layout.addWidget(self.bh2_name)

        # Color Palette Selector
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        self.palette_selector.currentTextChanged.connect(self.update_palette)
        layout.addWidget(QLabel("Color Palette:"))
        layout.addWidget(self.palette_selector)

        # Import Button
        btn_import = QPushButton("Import CSV")
        btn_import.clicked.connect(self.import_csv)
        layout.addWidget(btn_import)

        # Tables
        self.bh1_table = EnhancedTable()
        self.bh2_table = EnhancedTable()
        layout.addWidget(QLabel("Borehole 1 Data:"))
        layout.addWidget(self.bh1_table)
        layout.addWidget(QLabel("Borehole 2 Data:"))
        layout.addWidget(self.bh2_table)

        # Plot Controls
        control_layout = QGridLayout()
        self.plot_width = QSpinBox()
        self.plot_width.setRange(1, 50)
        self.plot_width.setValue(10)
        self.plot_gap = QSpinBox()
        self.plot_gap.setRange(0, 50)
        self.plot_gap.setValue(30)
        
        control_layout.addWidget(QLabel("Plot Width (m):"), 0, 0)
        control_layout.addWidget(self.plot_width, 0, 1)
        control_layout.addWidget(QLabel("Gap Between Plots (m):"), 1, 0)
        control_layout.addWidget(self.plot_gap, 1, 1)
        
        layout.addLayout(control_layout)
        layout.addWidget(QPushButton("Generate Plot", clicked=self.generate_plot))

        # Right Panel - Plot Area
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        right_panel = QWidget()
        plot_layout = QVBoxLayout(right_panel)
        plot_layout.addWidget(toolbar)
        plot_layout.addWidget(self.canvas)

        # Configure splitter
        main_splitter.addWidget(left_panel)
        main_splitter.addWidget(right_panel)
        main_splitter.setSizes([self.INPUT_WIDTH, self.width()-self.INPUT_WIDTH])

        self.setCentralWidget(main_splitter)

    def update_palette(self, palette_name):
        self.current_palette = palette_name
        self.generate_plot()

    def import_csv(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
            if not filename:
                return

            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    table = self.bh1_table if row['Borehole'] == '1' else self.bh2_table
                    
                    # Convert Layer No to integer (0-based index for table rows)
                    layer_no = int(row['Layer No']) - 1
                    
                    # Ensure table has enough rows
                    while table.rowCount() <= layer_no:
                        table.insertRow(table.rowCount())
                    
                    # Fill the table row
                    table.setItem(layer_no, 0, QTableWidgetItem(row['Layer Name']))
                    table.setItem(layer_no, 1, QTableWidgetItem(row['Start Level (m)']))
                    table.setItem(layer_no, 2, QTableWidgetItem(row['End Level (m)']))
                    table.setItem(layer_no, 3, QTableWidgetItem(row['SPT Value']))
                        
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Invalid CSV format: {str(e)}")

    def generate_plot(self):
        try:
            self.figure.clear()
            bh1_data = self.get_borehole_data(self.bh1_table)
            bh2_data = self.get_borehole_data(self.bh2_table)

            plot_width = self.plot_width.value()
            plot_gap = self.plot_gap.value()

            # Calculate width ratios based on real-world scale
            total_width = plot_width * 2 + plot_gap
            width_ratios = [plot_width, plot_width]
            wspace = plot_gap / total_width

            gs = self.figure.add_gridspec(1, 2, width_ratios=width_ratios, wspace=wspace)
            
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])

            # Get unique layer names and assign colors
            all_layers = set([layer['layer'] for layer in bh1_data + bh2_data])
            colors = self.get_layer_colors(all_layers)

            self.plot_borehole(ax1, bh1_data, self.bh1_name.text(), colors)
            self.plot_borehole(ax2, bh2_data, self.bh2_name.text(), colors)

            self.canvas.draw()

        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def get_layer_colors(self, layers):
        palette = self.COLOR_PALETTES[self.current_palette]
        return {layer: palette[i % len(palette)] for i, layer in enumerate(sorted(layers))}

    def get_borehole_data(self, table):
        data = []
        for row in range(table.rowCount()):
            items = [table.item(row, col) for col in range(4)]
            if not all(items):
                continue
                
            try:
                data.append({
                    'layer': items[0].text(),
                    'start': float(items[1].text()),
                    'end': float(items[2].text()),
                    'spt': int(items[3].text())
                })
            except ValueError:
                continue
                
        return sorted(data, key=lambda x: x['start'], reverse=True)

    def plot_borehole(self, ax, data, title, colors):
        if not data:
            return

        ax.set_title(title)
        ax.set_xticks([])
        ax.set_ylabel("Level (mSHD)")
        ax.grid(True, linestyle='--', alpha=0.7)

        for layer in data:
            thickness = abs(layer['end'] - layer['start'])
            ax.bar(0, thickness, width=1, bottom=layer['end'], 
                  color=colors[layer['layer']], edgecolor='black')
            
            ax.text(0.5, (layer['start'] + layer['end']) / 2,
                   f"{layer['layer']}\nSPT: {layer['spt']}",
                   ha='center', va='center')

        ax.set_ylim(data[-1]['end'] - 1, data[0]['start'] + 1)
        ax.invert_yaxis()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())