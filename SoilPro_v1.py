import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt


class EnhancedTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(["Layer Name", "Start Level\n(m)", "End Level\n(m)", "SPT Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.clipboard = QApplication.clipboard()
        self.setMinimumRowCount(15)

    def minimumRowCount(self):
        return max(15, self.rowCount())

    def setMinimumRowCount(self, count):
        while self.rowCount() < count:
            self.insertRow(self.rowCount())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.clearSelectedCells()
        else:
            super().keyPressEvent(event)

    def clearSelectedCells(self):
        for item in self.selectedItems():
            item.setText("")

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


class SoilProfileApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soil Stack Profile GUI")
        self.setGeometry(100, 100, 1200, 800)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        input_layout = QGridLayout()

        self.bh1_table = EnhancedTable(15, 4)
        input_layout.addWidget(QLabel("Borehole 1 Data:"), 0, 0)
        input_layout.addWidget(self.bh1_table, 1, 0)

        self.bh2_table = EnhancedTable(15, 4)
        input_layout.addWidget(QLabel("Borehole 2 Data:"), 0, 1)
        input_layout.addWidget(self.bh2_table, 1, 1)

        self.plot_width_input = QSpinBox()
        self.plot_width_input.setRange(1, 50)
        self.plot_width_input.setValue(10)
        self.plot_gap_input = QSpinBox()
        self.plot_gap_input.setRange(0, 50)
        self.plot_gap_input.setValue(15)
        input_layout.addWidget(QLabel("Plot Width (m):"), 2, 0)
        input_layout.addWidget(self.plot_width_input, 2, 1)
        input_layout.addWidget(QLabel("Gap Between Plots (m):"), 3, 0)
        input_layout.addWidget(self.plot_gap_input, 3, 1)

        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        self.import_button = QPushButton("Import Data")
        self.import_button.clicked.connect(self.import_data)
        input_layout.addWidget(self.export_button, 4, 0)
        input_layout.addWidget(self.import_button, 4, 1)

        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.clicked.connect(self.generate_plot)
        input_layout.addWidget(self.plot_button, 5, 0, 1, 2)

        self.figure, self.ax = plt.subplots(1, 2, figsize=(10, 10))
        self.canvas = FigureCanvas(self.figure)
        toolbar = NavigationToolbar(self.canvas, self)

        left_container = QWidget()
        left_container.setLayout(input_layout)
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(toolbar)
        plot_layout.addWidget(self.canvas)

        main_layout.addWidget(left_container, stretch=1)
        plot_container = QWidget()
        plot_container.setLayout(plot_layout)
        main_layout.addWidget(plot_container, stretch=2)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def generate_plot(self):
        borehole1 = self.get_borehole_data(self.bh1_table)
        borehole2 = self.get_borehole_data(self.bh2_table)
        widths = [self.plot_width_input.value(), self.plot_width_input.value()]
        gap_fraction = self.plot_gap_input.value() / sum(widths) * 10

        self.figure.clear()
        self.ax = self.figure.subplots(1, 2, gridspec_kw={"width_ratios": widths, "wspace": gap_fraction})

        self.plot_soil_stack(self.ax[0], borehole1, "Borehole 1")
        self.plot_soil_stack(self.ax[1], borehole2, "Borehole 2")

        self.canvas.draw()

    def get_borehole_data(self, table):
        data = []
        for row in range(table.rowCount()):
            layer = table.item(row, 0).text() if table.item(row, 0) else ""
            start = float(table.item(row, 1).text()) if table.item(row, 1) else 0
            end = float(table.item(row, 2).text()) if table.item(row, 2) else 0
            spt = int(table.item(row, 3).text()) if table.item(row, 3) else 0
            data.append({"layer": layer, "start": start, "end": end, "spt": spt})
        return data

    def plot_soil_stack(self, axis, borehole_data, title):
        for layer in borehole_data:
            axis.fill_betweenx([layer["start"], layer["end"]], 0, 1, label=f"{layer['layer']} (SPT={layer['spt']})")
        axis.invert_yaxis()
        axis.set_title(title)
        axis.legend(loc="best")
        axis.set_xlim(0, 1)
        axis.set_xticks([])
        axis.set_ylabel("Depth (m)")

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if path:
            data = self.get_borehole_data(self.bh1_table)
            df = pd.DataFrame(data)
            if path.endswith('.csv'):
                df.to_csv(path, index=False)
            else:
                df.to_excel(path, index=False)

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;Excel Files (*.xlsx)")
        if path:
            if path.endswith('.csv'):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            self.load_data_into_table(df)

    def load_data_into_table(self, df):
        self.bh1_table.setRowCount(0)
        self.bh2_table.setRowCount(0)
        for i, row in df.iterrows():
            self.bh1_table.insertRow(i)
            self.bh2_table.insertRow(i)
            for j, value in enumerate(row):
                self.bh1_table.setItem(i, j, QTableWidgetItem(str(value)))
                self.bh2_table.setItem(i, j, QTableWidgetItem(str(value)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
