import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QFileDialog, QLineEdit
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
        self.setHorizontalHeaderLabels(["Layer Name", "Start Level (m)", "End Level (m)", "SPT Value"])
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

        # Add borehole name fields
        self.bh1_name = QLineEdit("Borehole 1")
        self.bh1_name.setToolTip("Enter the name for Borehole 1")
        self.bh2_name = QLineEdit("Borehole 2")
        self.bh2_name.setToolTip("Enter the name for Borehole 2")
        input_layout.addWidget(QLabel("Borehole 1 Name:"), 0, 0)
        input_layout.addWidget(self.bh1_name, 0, 1)
        input_layout.addWidget(QLabel("Borehole 2 Name:"), 1, 0)
        input_layout.addWidget(self.bh2_name, 1, 1)

        # Add tables
        self.bh1_table = EnhancedTable(15, 4)
        self.bh1_table.setToolTip("Enter data for Borehole 1")
        input_layout.addWidget(QLabel("Borehole 1 Data:"), 2, 0)
        input_layout.addWidget(self.bh1_table, 3, 0)

        self.bh2_table = EnhancedTable(15, 4)
        self.bh2_table.setToolTip("Enter data for Borehole 2")
        input_layout.addWidget(QLabel("Borehole 2 Data:"), 2, 1)
        input_layout.addWidget(self.bh2_table, 3, 1)

        # Plot width and gap controls
        self.plot_width_input = QSpinBox()
        self.plot_width_input.setRange(1, 50)
        self.plot_width_input.setValue(10)
        self.plot_width_input.setToolTip("Set the width of the plot")
        self.plot_gap_input = QSpinBox()
        self.plot_gap_input.setRange(0, 50)
        self.plot_gap_input.setValue(15)
        self.plot_gap_input.setToolTip("Set the gap between the plots")
        input_layout.addWidget(QLabel("Plot Width (m):"), 4, 0)
        input_layout.addWidget(self.plot_width_input, 4, 1)
        input_layout.addWidget(QLabel("Gap Between Plots (m):"), 5, 0)
        input_layout.addWidget(self.plot_gap_input, 5, 1)

        # Buttons
        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.setToolTip("Generate the soil profile plot")
        self.plot_button.clicked.connect(self.generate_plot)
        input_layout.addWidget(self.plot_button, 6, 0, 1, 2)

        # Matplotlib canvas
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
        try:
            borehole1 = self.get_borehole_data(self.bh1_table)
            borehole2 = self.get_borehole_data(self.bh2_table)
            if not borehole1 or not borehole2:
                QMessageBox.warning(self, "Error", "Please enter valid data for both boreholes.")
                return

            widths = [self.plot_width_input.value(), self.plot_width_input.value()]
            gap_fraction = self.plot_gap_input.value() / sum(widths) * 10

            self.figure.clear()
            self.ax = self.figure.subplots(1, 2, gridspec_kw={"width_ratios": widths, "wspace": gap_fraction})

            self.plot_soil_stack(self.ax[0], borehole1, self.bh1_name.text())
            self.plot_soil_stack(self.ax[1], borehole2, self.bh2_name.text())

            self.canvas.draw()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def get_borehole_data(self, table):
        data = []
        for row in range(table.rowCount()):
            layer = table.item(row, 0).text().strip() if table.item(row, 0) and table.item(row, 0).text() else ""
            start = table.item(row, 1).text().strip() if table.item(row, 1) and table.item(row, 1).text() else ""
            end = table.item(row, 2).text().strip() if table.item(row, 2) and table.item(row, 2).text() else ""
            spt = table.item(row, 3).text().strip() if table.item(row, 3) and table.item(row, 3).text() else ""

            if not any([layer, start, end, spt]):
                continue

            try:
                start = float(start)
                end = float(end)
                spt = int(spt)
            except ValueError:
                continue

            data.append({"layer": layer, "start": start, "end": end, "spt": spt})

        return data

    def plot_soil_stack(self, axis, borehole_data, title):
        if not borehole_data:
            return

        for layer in borehole_data:
            axis.fill_betweenx([layer["start"], layer["end"]], 0, 1, color="skyblue")
            axis.text(0.5, (layer["start"] + layer["end"]) / 2, f"{layer['layer']} ({layer['spt']})", ha="center")
        axis.set_ylim(max(borehole_data, key=lambda x: x["end"])["end"], min(borehole_data, key=lambda x: x["start"])["start"])
        axis.set_title(title)
        axis.set_xticks([])
        axis.set_ylabel("Level (mSHD)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())