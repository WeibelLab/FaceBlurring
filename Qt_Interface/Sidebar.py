
from Video import VideoWidget
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QDockWidget, QFileDialog, QHBoxLayout, QPushButton, QWidget
from PyQt5.QtCore import Qt
import os, shutil, atexit

class SidebarWidget(QWidget): #QDock

    def __init__(self, parent, video_blurring_window):
        QWidget.__init__(self, parent)
        self.video_blurring_window = video_blurring_window
        self.metaObject().className()
        self.setLayout(QHBoxLayout())

        # print(help(self))
        # self.setAttribute("className", "SidebarWidget") # FIXME: works?

        self.loadButton = QPushButton()
        self.loadButton.setText("Load File")
        self.loadButton.clicked.connect(self.loadVideo)
        self.layout().addWidget(self.loadButton)

        self.setMinimumSize(300, 800)

    @property
    def videoSpace(self):
        return self.window().findChild(QWidget, "Video Space")


    def loadVideo(self):
        path, _ = QFileDialog.getOpenFileName(None, "Open Movie", QDir.currentPath())
        if (not path): # user cancels selection
            return None

        video = self._duplicate_and_load(self, path)
        if (isinstance(video, QDockWidget)):
            self.videoSpace.addDockWidget(Qt.LeftDockWidgetArea, video)
        else:
            self.videoSpace.layout().addWidget(video)
        
    
    @staticmethod
    def _duplicate_and_load(sidebar, path):
        '''Loads video from a path
        @param {str} path the path to the video. If None will open file selection window

        Loading process will create a copy of the video in a 'tmp' folder.
        Changes in the UI will not overwrite the original video
        '''


        # Load Video
        # Move video to tmp folder
        absolute_path = os.path.abspath(path)
        folder = os.path.dirname(absolute_path)
        temp_folder = os.path.join(folder, "tmp")
        filename = absolute_path.replace(folder, "").strip("\\").strip("/")

        # Create temp folder
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder) # make folder
            def removeFolder(folder):
                print("Removing folder", folder)
                os.removedirs(folder)
            atexit.register(removeFolder, folder=temp_folder) # only gets removed by whichever video created it

        # Create temp file
        path = os.path.join(temp_folder, "_"+filename)
        shutil.copyfile(absolute_path, path) # copy file so we can edit it
        def remove(filepath):
            print("Removing file", filepath)
            os.remove(filepath)
        atexit.register(remove, filepath=path)

        instance = VideoWidget(filename, path=path, toolbar=sidebar.video_blurring_window.toolbar)
        instance.playButton.setEnabled(True)
        return instance