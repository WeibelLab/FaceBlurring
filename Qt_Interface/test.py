from PyQt5.QtGui import QPalette
import cv2, numpy, atexit
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import *

app = QApplication([])
window = QWidget()
window.setLayout(QVBoxLayout())
window.capture_the_flag = "Capture me"

scrollAreaWidget = QWidget()
scrollAreaWidget.setLayout(QVBoxLayout())
window.layout().addWidget(scrollAreaWidget)

scrollAreaWidget.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

for i in range(100):
    lab = QLabel()
    lab.setText("Hello World how are you doing today?")
    scrollAreaWidget.layout().addWidget(lab)

else:
    print(lab.window().layout().children()[0])


window.show()
app.exec_()

