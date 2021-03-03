from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QDockWidget, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget
import Video, Sidebar, Toolbar

class VideoBlurring(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # Upper
        self.upper = QWidget()
        self.upper.setLayout(QHBoxLayout())
        self.layout().addWidget(self.upper)
        self.upper.setObjectName("Upper Frame")

        # Bottom Timeline
        self.timeline = QWidget()
        self.layout().addWidget(self.timeline)
        self.timeline.setMinimumHeight(100)
        self.timeline.setObjectName("Timeline Container")

        # Center for videos
        self.videoSpace = QWidget() #QMainWindow()
        self.videoSpace.setLayout(QVBoxLayout())
        self.videoSpace.setObjectName("Video Space")

        # Sidebar
        self.sidebar = Sidebar.SidebarWidget(None, self)
        self.sidebar.setObjectName("Sidebar")
        # Toolbar
        self.toolbar = Toolbar.Toolbar(None, self)
        self.toolbar.setObjectName("Toolbar")
        # Add to GUI
        self.upper.layout().addWidget(self.sidebar)
        self.upper.layout().addWidget(self.toolbar)
        self.upper.layout().addWidget(self.videoSpace)