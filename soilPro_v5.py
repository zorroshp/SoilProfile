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
    HEADER_HEIGHT = 60
    COLUMN_WIDTHS = [120, 100, 100, 80]
    COLUMN_PADDING = 15

    def __init__(self, parent=None):
        super().__init__(15, 4)
        self.setup_table()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def setup_table(self):
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
            self.copy_selection()
        elif action == paste_action:
            self.paste_selection()
        elif action == delete_action:
            self.clear_selection()

    def copy_selection(self):
        selected = self.selectedRanges()
        if not selected: return
        
        text = ""
        for range in selected:
            for row in range(range.topRow(), range.bottomRow()+1):
                for col in range(range.leftColumn(), range.rightColumn()+1):
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
        self.init_ui()
        self.setWindowTitle("Geotechnical Profile Analyzer")
        self.setGeometry(100, 100, 1400, 900)

    def init_ui(self):
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel
        left_panel = QWidget()
        layout = QVBoxLayout(left_panel)
        
        # Controls
        self.bh1_name = QLineEdit("Borehole-1")
        self.bh2_name = QLineEdit("Borehole-2")
        self.palette_selector = QComboBox()
        self.palette_selector.addItems(self.COLOR_PALETTES.keys())
        
        # Plot controls
        self.plot_width = QSpinBox()
        self.plot_width.setRange(1, 100)
        self.plot_width.setValue(2)
        self.plot_gap = QSpinBox()
        self.plot_gap.setRange(0, 100)
        self.plot_gap.setValue(15)
        
        # Layout organization
        layout.addWidget(QLabel("Borehole Names:"))
        layout.addWidget(self.bh1_name)
        layout.addWidget(self.bh2_name)
        layout.addWidget(QLabel("Color Palette:"))
        layout.addWidget(self.palette_selector)
        layout.addWidget(QPushButton("Import CSV", clicked=self.import_csv))
        
        # Tables
        layout.addWidget(QLabel("Borehole 1 Data:"))
        self.bh1_table = EnhancedTable()
        layout.addWidget(self.bh1_table)
        layout.addWidget(QLabel("Borehole 2 Data:"))
        self.bh2_table = EnhancedTable()
        layout.addWidget(self.bh2_table)
        
        # Plot controls
        controls = QGridLayout()
        controls.addWidget(QLabel("Profile Width (m):"), 0, 0)
        controls.addWidget(self.plot_width, 0, 1)
        controls.addWidget(QLabel("Borehole Spacing (m):"), 1, 0)
        controls.addWidget(self.plot_gap, 1, 1)
        layout.addLayout(controls)
        layout.addWidget(QPushButton("Generate Profile", clicked=self.generate_plot))

        # Right Panel
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
        try:
            filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
            if not filename: return
            
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
            
            # Get data and parameters
            bh1_data = self.get_borehole_data(self.bh1_table)
            bh2_data = self.get_borehole_data(self.bh2_table)
            plot_width = self.plot_width.value()
            plot_gap = self.plot_gap.value()
            
            # Calculate gridspec parameters
            width_ratios = [1, 1]
            wspace = plot_gap / plot_width  # Direct ratio calculation
            
            # Create plot layout
            gs = self.figure.add_gridspec(1, 2, width_ratios=width_ratios, wspace=wspace)
            ax1 = self.figure.add_subplot(gs[0])
            ax2 = self.figure.add_subplot(gs[1])
            
            # Assign colors
            all_layers = sorted({layer['layer'] for layer in bh1_data + bh2_data})
            colors = self.get_colors(all_layers)
            
            # Plot profiles
            self.plot_profile(ax1, bh1_data, self.bh1_name.text(), colors, plot_width)
            self.plot_profile(ax2, bh2_data, self.bh2_name.text(), colors, plot_width)
            
            self.canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "Plot Error", str(e))

    def get_colors(self, layers):
        palette = self.COLOR_PALETTES[self.palette_selector.currentText()]
        return {layer: palette[i % 12] for i, layer in enumerate(layers)}

    def get_borehole_data(self, table):
        data = []
        for row in range(table.rowCount()):
            items = [table.item(row, col) for col in range(4)]
            if not all(items): continue
            
            try:
                data.append({
                    'layer': items[0].text(),
                    'start': float(items[1].text()),
                    'end': float(items[2].text()),
                    'spt': int(items[3].text())
                })
            except ValueError:
                continue
                
        return sorted(data, key=lambda x: x['start'], reverse=False)  # Reverse removed

    def plot_profile(self, ax, data, title, colors, plot_width):
        if not data: return
        
        ax.set_title(title, pad=20)
        ax.set_xticks([])
        ax.set_ylabel("Elevation (mSHD)", labelpad=15)
        ax.grid(True, linestyle='--', alpha=0.5)
        
        # Set aspect ratio for scale consistency
        ax.set_aspect('equal', adjustable='box')
        
        # Set x-axis limits based on plot width
        ax.set_xlim(-plot_width/2, plot_width/2)
        
        # Plot layers from top to bottom
        for layer in data:
            thickness = abs(layer['end'] - layer['start'])
            ax.bar(0, thickness, width=plot_width, 
                   bottom=layer['start'],  # Use start level as bottom
                   color=colors[layer['layer']], 
                   edgecolor='black', 
                   linewidth=0.5)
            
            ax.text(0, (layer['start'] + layer['end']) / 2,
                   f"{layer['layer']}\nSPT: {layer['spt']}",
                   ha='center', va='center', fontsize=9)
        
        # Set y-axis limits with buffer
        y_min = min(layer['end'] for layer in data) - 1
        y_max = max(layer['start'] for layer in data) + 1
        ax.set_ylim(y_min, y_max)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
