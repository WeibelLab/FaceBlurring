from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QDockWidget, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget
from VideoBlurringWindow import *

# Create Window with widget
app = QApplication([])
# Set Stylesheet
# qss = "./Qt_Interface/darktheme.qss"
# with open(qss, 'r') as f:
#     app.setStyleSheet("\n".join(f.readlines()))

window = VideoBlurring()
window.show()
app.exec()
print("Closed")