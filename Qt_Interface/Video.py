
from PyQt5.QtCore import QDir, QUrl, Qt
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QMainWindow, QPushButton, QSlider, QWidget, QVBoxLayout


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

        # Load video if exists
        self.path = path
        if (self.path):
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(self.path)))
            self.playButton.setEnabled(True)




    def loadVideo(path=None, instance=None):
        '''Loads video from a path
        @param {str} path the path to the video. If None will open file selection window
        @param {Video} instance the object to assign the video to. Creates a new isntance if None
        '''
        if (not path): # set path if doesn't exist
            path, _ = QFileDialog.getOpenFileName(None, "Open Movie", QDir.currentPath())
        
        if (not path): # user cancels selection
            return None

        if (instance is None): # spawn if no instance
            instance = VideoWidget()

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