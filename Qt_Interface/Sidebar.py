
from Video import VideoWidget
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QDockWidget, QFileDialog, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt
import os, shutil, atexit
import cv2

class SidebarWidget(QWidget): #QDock

    def __init__(self, parent, video_blurring_window):
        QWidget.__init__(self, parent)
        self.video_blurring_window = video_blurring_window
        self.metaObject().className()
        self.setLayout(QVBoxLayout())

        # print(help(self))
        # self.setAttribute("className", "SidebarWidget") # FIXME: works?

        self.loadButton = QPushButton()
        self.loadButton.setText("Load File")
        self.loadButton.clicked.connect(self.loadVideo)
        self.layout().addWidget(self.loadButton)

        self.exportButton = QPushButton()
        self.exportButton.setText("Export")
        self.exportButton.clicked.connect(self.exportVideos)
        self.layout().addWidget(self.exportButton)

        self.setMinimumSize(300, 800)

    @property
    def videoSpace(self):
        return self.window().findChild(QWidget, "Video Space")


    def loadVideo(self):
        path, _ = QFileDialog.getOpenFileName(None, "Open Movie", QDir.currentPath() + "../sample_assets/")
        if (not path): # user cancels selection
            return None

        video = self._load(self, path)
        if (isinstance(video, QDockWidget)):
            self.videoSpace.addDockWidget(Qt.LeftDockWidgetArea, video)
        else:
            self.videoSpace.layout().addWidget(video)
        
    
    @staticmethod
    def _load(sidebar, path):
        '''Loads video from a path
        @param {str} path the path to the video. If None will open file selection window

        Loading process will create a copy of the video in a 'tmp' folder.
        Changes in the UI will not overwrite the original video
        '''


        # Load Video
        absolute_path = os.path.abspath(path)
        path = absolute_path
        folder = os.path.dirname(absolute_path)
        filename = absolute_path.replace(folder, "").strip("\\").strip("/")

        instance = VideoWidget(filename, path=absolute_path, toolbar=sidebar.video_blurring_window.toolbar)
        instance.playButton.setEnabled(True)
        return instance

    def exportVideos(self):
        path = QFileDialog.getExistingDirectory(None, "Select Save Location", QDir.currentPath())
        if (not path): # user cancels selection
            return None
        print("Exporting to", path)

        # Render each video with blurring
        for widget in VideoWidget.Widgets:
            outFilename = os.path.join(path, os.path.splitext(os.path.basename(widget.video._video_path))[0]+"_blurred.mp4")
            widget.export(outFilename)
