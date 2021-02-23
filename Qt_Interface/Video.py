
from PyQt5 import QtGui
from PyQt5.QtCore import QDir, QUrl, Qt
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QPushButton, QSlider, QWidget, QVBoxLayout

import cv2, os, shutil, atexit, numpy
from BlurObject import *
class VideoWidget(QWidget): #QDock

    def __init__(self, path=None):
        super().__init__()

        # Structure
        self.setLayout(QVBoxLayout())

        # Buttons
        self.buttonRow = QWidget()
        self.buttonRowLayout = QHBoxLayout()
        self.buttonRow.setLayout(self.buttonRowLayout)
        
        self.playButton = QPushButton()
        self.playButton.setText("Play")
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play)

        self.progressSlider = QSlider(Qt.Horizontal)
        self.progressSlider.setRange(0, 0)
        self.progressSlider.sliderMoved.connect(self.setPosition)

        self.buttonRowLayout.addWidget(self.playButton)
        self.buttonRowLayout.addWidget(self.progressSlider)

        # Video
        self.videoWidget = QVideoWidget()
        self.player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.player.setVideoOutput(self.videoWidget)
        self.player.stateChanged.connect(self.__onPlayerStateChange)
        self.player.positionChanged.connect(self.__onPositionSet)
        self.player.durationChanged.connect(self.__onVideoDurationChange)
        self.videoWidget.setMinimumSize(640, 480)

        # Add widgets to self
        self.layout().addWidget(self.videoWidget)
        self.layout().addWidget(self.buttonRow)
        
        # Set Blurring variables
        self._blur_strands = []
        self._blur_object = None

        # Load video if exists
        self.path = path
        self._video = None
        if (path):
            VideoWidget.loadVideo(self.path, self)

    @property
    def display_resolution(self):
        return self.videoWidget.size().width(), self.videoWidget.size().height() # FIXME: get displayed video's resolution

    @property
    def video_resolution(self):
        return (1920, 1080) # TODO: Implement



    def loadVideo(path=None, instance=None):
        '''Loads video from a path
        @param {str} path the path to the video. If None will open file selection window
        @param {Video} instance the object to assign the video to. Creates a new isntance if None

        Loading process will create a copy of the video in a 'tmp' folder.
        Changes in the UI will not overwrite the original video
        '''
        if (not path): # set path if doesn't exist
            path, _ = QFileDialog.getOpenFileName(None, "Open Movie", QDir.currentPath())
        
        if (not path): # user cancels selection
            return None

        if (instance is None): # spawn if no instance
            instance = VideoWidget()

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

        # Open file with OpenCV
        # instance._video = cv2.VideoCapture(path)
        # atexit.register(instance._video.release)

        # assign video
        instance.player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
        instance.playButton.setEnabled(True)
        return instance

    def load(self, path=None):
        '''Loads video from a path
        @param {str} path the path to the video. If None will open file selection window
        '''
        VideoWidget.loadVideo(path, self)

    def play(self):
        ''' plays or pauses video '''
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def __onPlayerStateChange(self, state):
        ''' changes the play/pause button depending on state '''
        if self.player.state() == QMediaPlayer.PlayingState:
            self.playButton.setText("Pause")
        else:
            self.playButton.setText("Play")

    def __onPositionSet(self, pos):
        self.progressSlider.setValue(pos)

    def setPosition(self, pos):
        ''' Sets the current playback position of the video '''
        self.player.setPosition(pos)

    def __onVideoDurationChange(self, duration):
        self.progressSlider.setRange(0, duration)


    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._blur_object = BlurStrand(self, self.display_resolution, self.video_resolution)
        self._blur_strands.append(self._blur_object)
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        # Get click location in movie's space
        self._blur_object.addPoint(
            self.player.position(),
            (a0.localPos().x(), a0.localPos().y()),
            5, # TODO: Implement brush size
            self.display_resolution
        )
        return super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        print("Released", self._blur_object)
        self._blur_object = None
        return super().mouseReleaseEvent(a0)