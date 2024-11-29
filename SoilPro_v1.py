import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QSpinBox, QHBoxLayout, QHeaderView, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QClipboard
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
from PyQt5.QtWidgets import QMessageBox
import matplotlib.pyplot as plt


class EnhancedTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(["Layer Name", "Start Level (m)", "End Level (m)", "SPT Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
        self.clipboard = QApplication.clipboard()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_clipboard()
        elif event.key() == Qt.Key_V and (event.modifiers() & Qt.ControlModifier):
            self.paste_clipboard()
        else:
            super().keyPressEvent(event)

    def copy_clipboard(self):
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return  # No selection to copy

        text = ""
        for selected_range in selected_ranges:
            for row in range(selected_range.topRow(), selected_range.bottomRow() + 1):
                for col in range(selected_range.leftColumn(), selected_range.rightColumn() + 1):
                    item = self.item(row, col)
                    if item is not None:  # Check if the item exists before accessing text
                        text += item.text() + '\t'
                    else:
                        text += '\t'  # Append a tab for empty cells
                text = text.rstrip('\t') + '\n'  # Remove the last tab and append a newline

        self.clipboard.setText(text.strip())  # Set the text to the clipboard, stripping the last newline


    def paste_clipboard(self):
        text = self.clipboard.text()
        rows = text.split('\n')
        current_row = self.currentRow()
        current_col = self.currentColumn()
        for r, row in enumerate(rows):
            if row.strip() != '':
                cells = row.split('\t')
                for c, text in enumerate(cells):
                    row_position = current_row + r
                    col_position = current_col + c
                    if row_position < self.rowCount() and col_position < self.columnCount():
                        self.setItem(row_position, col_position, QTableWidgetItem(text))
                    else:
                        self.insertRow(row_position)
                        self.setItem(row_position, col_position, QTableWidgetItem(text))

    def context_menu(self, position):
        menu = QMenu()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == copy_action:
            self.copy_clipboard()
        elif action == paste_action:
            self.paste_clipboard()


class SoilProfileApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Soil Stack Profile GUI")
        self.setGeometry(100, 100, 1200, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        input_layout = QGridLayout()

        self.bh1_table = EnhancedTable(4, 4)
        input_layout.addWidget(QLabel("Borehole 1 Data:"), 0, 0)
        input_layout.addWidget(self.bh1_table, 1, 0)

        self.bh2_table = EnhancedTable(4, 4)
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

        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.clicked.connect(self.generate_plot)
        input_layout.addWidget(self.plot_button, 4, 0, 1, 2)

        self.figure, self.ax = plt.subplots(1, 2, figsize=(8, 8))
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
