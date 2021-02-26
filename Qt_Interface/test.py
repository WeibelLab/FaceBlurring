from PyQt5.QtGui import QPalette
import cv2, numpy, atexit
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import *

app = QApplication([])
window = QWidget()
window.setLayout(QVBoxLayout())

scrollAreaWidget = QWidget()
scrollAreaWidget.setLayout(QVBoxLayout())
window.layout().addWidget(scrollAreaWidget)

scrollAreaWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

scrollArea = QScrollArea(scrollAreaWidget)
scrollArea.setBackgroundRole(QPalette.Window)
scrollArea.setFrameShadow(QFrame.Plain)
scrollArea.setFrameShape(QFrame.NoFrame)
scrollArea.setWidgetResizable(True)
scrollAreaWidget.layout().addWidget(scrollArea)
scrollArea.setWidget(scrollAreaWidget)

for i in range(100):
    lab = QLabel()
    lab.setText("Hello World how are you doing today?")
    scrollAreaWidget.layout().addWidget(lab)


window.show()
app.exec_()

