"""
Module: input_table.py
This module defines the InputTable widget—a customized QTableWidget for entering borehole layer data.
It includes preset headers, fixed row heights, and a context menu for copy, paste, and clear operations.
"""

import sys
from library import QApplication, QTableWidget, QTableWidgetItem, QMenu, Qt

class InputTable(QTableWidget):
    """
    Custom table widget for inputting borehole data.
    """
    HEADER_HEIGHT = 40
    COLUMN_WIDTHS = [120, 80, 80, 80]
    COLUMN_PADDING = 10

    def __init__(self, parent=None):
        super().__init__(15, 4, parent)
        self.setup_table()
        self.clipboard = QApplication.clipboard()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def setup_table(self):
        """
        Set up the table with predefined column headers and widths.
        """
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
        self.verticalHeader().setDefaultSectionSize(30)

    def show_context_menu(self, position):
        """
        Display a context menu with Copy, Paste, and Clear actions.
        """
        menu = QMenu()
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        clear_action = menu.addAction("Clear")
        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == copy_action:
            self.copy_selected_cells()
        elif action == paste_action:
            self.paste_cells()
        elif action == clear_action:
            self.clear_selected_cells()

    def copy_selected_cells(self):
        """
        Copy the selected table cells to the clipboard.
        """
        selected_ranges = self.selectedRanges()
        if not selected_ranges:
            return
        text = ""
        for rng in selected_ranges:
            for row in range(rng.topRow(), rng.bottomRow() + 1):
                for col in range(rng.leftColumn(), rng.rightColumn() + 1):
                    item = self.item(row, col)
                    text += (item.text() if item else "") + "\t"
                text = text.rstrip() + "\n"
        self.clipboard.setText(text.strip())

    def paste_cells(self):
        """
        Paste clipboard text into the table starting at the current cell.
        """
        text = self.clipboard.text()
        rows = text.split("\n")
        current_row = self.currentRow()
        current_col = self.currentColumn()
        for r, row_text in enumerate(rows):
            cells = row_text.split("\t")
            for c, cell_text in enumerate(cells):
                target_row = current_row + r
                target_col = current_col + c
                if target_row < self.rowCount() and target_col < self.columnCount():
                    self.setItem(target_row, target_col, QTableWidgetItem(cell_text.strip()))

    def clear_selected_cells(self):
        """
        Clear the text in all selected cells.
        """
        for item in self.selectedItems():
            item.setText("")

    def keyPressEvent(self, event):
        """
        Override the Delete key to clear selected cells.
        """
        if event.key() == Qt.Key_Delete:
            self.clear_selected_cells()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    from library import QApplication, QWidget, QVBoxLayout
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    table = InputTable()
    layout.addWidget(table)
    window.show()
    sys.exit(app.exec_())
