
from PyQt5.QtGui import QKeySequence
from Video import VideoWidget
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QDockWidget, QFileDialog, QShortcut, QVBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt
import os, shutil, atexit
import cv2, uuid, json

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
        self.exportButton.setText("Export All (broken)")
        self.exportButton.clicked.connect(self.exportVideos)
        self.layout().addWidget(self.exportButton)

        self.saveButton = QPushButton()
        self.saveButton.setText("Save As")
        self.saveButton.clicked.connect(self.save)
        self.layout().addWidget(self.saveButton)

        self.saveShortcut = QShortcut(QKeySequence('Ctrl+S'), self)
        self.saveShortcut.activated.connect(self.save)

        self.__save_location = None


        self.setMinimumSize(300, 800)

    @property
    def videoSpace(self):
        return self.window().findChild(QWidget, "Video Space")


    def loadVideo(self):
        paths, _ = QFileDialog.getOpenFileNames(None, "Open Movie", QDir.currentPath())
        if not paths or len(paths) == 0: # user cancels selection
            return None
        for path in paths:
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

    def save(self):
        if self.__save_location is None:
            path, _ = QFileDialog.getSaveFileName(None, "Export As", QDir.currentPath(), "Video Blur File (*.vibf)")
            if (not path): # user cancels selection
                return
            
            self.__save_location = path
            self.saveButton.setText("Save")

        
        data = {
            "uuid": str(uuid.uuid4()),
            "videos": [],
        }

        for widget in VideoWidget.Widgets:
            videoData = {
                "name": widget.video._video_path,
                "blurstrands": []
            }
            for strand in widget.video._blur_strands:
                videoData["blurstrands"].append(strand.serialize())
            data["videos"].append(videoData)

        with open(self.__save_location, "w") as file:
            file.write(json.dumps(data))

