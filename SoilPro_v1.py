import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QGridLayout,
    QWidget, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QSpinBox, QHBoxLayout, QHeaderView, QMenu, QMessageBox, QFileDialog, QLineEdit
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar
)
import matplotlib.pyplot as plt


class EnhancedTable(QTableWidget):
    def __init__(self, rows, columns):
        super().__init__(rows, columns)
        self.setHorizontalHeaderLabels(["Layer Name", "Start Level (m)", "End Level (m)", "SPT Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)
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

    def context_menu(self, position):
        menu = QMenu()
        delete_action = menu.addAction("Clear")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == delete_action:
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
        self.bh2_name = QLineEdit("Borehole 2")
        input_layout.addWidget(QLabel("Borehole 1 Name:"), 0, 0)
        input_layout.addWidget(self.bh1_name, 0, 1)
        input_layout.addWidget(QLabel("Borehole 2 Name:"), 1, 0)
        input_layout.addWidget(self.bh2_name, 1, 1)

        # Add tables
        self.bh1_table = EnhancedTable(15, 4)
        input_layout.addWidget(QLabel("Borehole 1 Data:"), 2, 0)
        input_layout.addWidget(self.bh1_table, 3, 0)

        self.bh2_table = EnhancedTable(15, 4)
        input_layout.addWidget(QLabel("Borehole 2 Data:"), 2, 1)
        input_layout.addWidget(self.bh2_table, 3, 1)

        # Plot width and gap controls
        self.plot_width_input = QSpinBox()
        self.plot_width_input.setRange(1, 50)
        self.plot_width_input.setValue(10)
        self.plot_gap_input = QSpinBox()
        self.plot_gap_input.setRange(0, 50)
        self.plot_gap_input.setValue(15)
        input_layout.addWidget(QLabel("Plot Width (m):"), 4, 0)
        input_layout.addWidget(self.plot_width_input, 4, 1)
        input_layout.addWidget(QLabel("Gap Between Plots (m):"), 5, 0)
        input_layout.addWidget(self.plot_gap_input, 5, 1)

        # Buttons
        self.plot_button = QPushButton("Generate Plot")
        self.plot_button.clicked.connect(self.generate_plot)
        self.export_button = QPushButton("Export Data")
        self.export_button.clicked.connect(self.export_data)
        self.import_button = QPushButton("Import Data")
        self.import_button.clicked.connect(self.import_data)
        input_layout.addWidget(self.plot_button, 6, 0)
        input_layout.addWidget(self.export_button, 6, 1)
        input_layout.addWidget(self.import_button, 7, 0, 1, 2)

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
        borehole1 = self.get_borehole_data(self.bh1_table)
        borehole2 = self.get_borehole_data(self.bh2_table)
        widths = [self.plot_width_input.value(), self.plot_width_input.value()]
        gap_fraction = self.plot_gap_input.value() / sum(widths) * 10

        self.figure.clear()
        self.ax = self.figure.subplots(1, 2, gridspec_kw={"width_ratios": widths, "wspace": gap_fraction})

        self.plot_soil_stack(self.ax[0], borehole1, self.bh1_name.text())
        self.plot_soil_stack(self.ax[1], borehole2, self.bh2_name.text())

        self.canvas.draw()

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
        for layer in borehole_data:
            axis.fill_betweenx([layer["start"], layer["end"]], 0, 1, color="skyblue")
            axis.text(-0.1, (layer["start"] + layer["end"]) / 2, f"{layer['layer']} ({layer['spt']})", ha="right")
        axis.set_ylim(max(borehole_data, key=lambda x: x["end"])["end"], min(borehole_data, key=lambda x: x["start"])["start"])
        axis.set_title(title)
        axis.set_xticks([])
        axis.set_ylabel("Level (mSHD)")

    def export_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv)")
        if path:
            bh1_data = self.get_borehole_data(self.bh1_table)
            bh2_data = self.get_borehole_data(self.bh2_table)
            df1 = pd.DataFrame(bh1_data)
            df2 = pd.DataFrame(bh2_data)
            df1["Borehole"] = "Borehole 1"
            df2["Borehole"] = "Borehole 2"
            final_df = pd.concat([df1, df2])
            final_df.to_csv(path, index=False)

    def import_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv)")
        if path:
            df = pd.read_csv(path)
            self.load_data_into_table(df, "Borehole 1", self.bh1_table)
            self.load_data_into_table(df, "Borehole 2", self.bh2_table)

    def load_data_into_table(self, df, borehole_name, table):
        table.setRowCount(0)
        filtered_df = df[df['Borehole'] == borehole_name]
        for i, row in filtered_df.iterrows():
            row_idx = table.rowCount()
            table.insertRow(row_idx)
            for j, col_name in enumerate(["Layer Name", "Start Level (m)", "End Level (m)", "SPT Value"]):
                item = QTableWidgetItem(str(row[col_name]))
                item.setFlags(item.flags() | Qt.ItemIsEditable)
                table.setItem(row_idx, j, item)
        table.setMinimumRowCount(15)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SoilProfileApp()
    window.show()
    sys.exit(app.exec_())
