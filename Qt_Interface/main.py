from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QDockWidget, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget
import Video, Sidebar

# Create Window with widget
app = QApplication([])
window = QWidget()
layout = QVBoxLayout()
window.setLayout(layout)


# Set Stylesheet
# qss = "./darktheme.qss"
# with open(qss, 'r') as f:
#     app.setStyleSheet("\n".join(f.readlines()))

# Upper
upper = QWidget()
upperLayout = QHBoxLayout()
upper.setLayout(upperLayout)
layout.addWidget(upper)

# Bottom Timeline
timeline = QWidget()
layout.addWidget(timeline)
timeline.setMinimumHeight(100)

# Center for videos
videoSpace = QWidget() #QMainWindow()
videoSpace.setLayout(QVBoxLayout())

# Sidebar
sidebar = Sidebar.SidebarWidget(None, videoSpace)

# Add to GUI
upperLayout.addWidget(sidebar)
upperLayout.addWidget(videoSpace)



window.show()
app.exec_()