"""
Module: library.py
This module centralizes all third‐party library imports used by the application.
"""

import sys
import csv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QGridLayout, QSplitter,
    QWidget, QLabel, QPushButton, QLineEdit, QFileDialog, QComboBox, QCheckBox,
    QSpinBox, QDoubleSpinBox, QGroupBox, QFrame, QMessageBox, QTableWidget, QTableWidgetItem, QMenu
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QT as NavigationToolbar
