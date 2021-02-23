
from PyQt5 import QtGui
from PyQt5.QtCore import QDir, QUrl, Qt, QThread, pyqtSignal, QMutex
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QStackedLayout, QWidget, QVBoxLayout
from PyQt5.QtGui import QFont, QImage, QPixmap

import cv2, os, shutil, atexit, numpy, time
from BlurObject import *



class VideoThread(QThread):
    changePixmap = pyqtSignal(QImage)
    newFrame = pyqtSignal(numpy.ndarray)
    stateChanged = pyqtSignal(bool) # True for playing started. False for playing stopped
    positionChanged = pyqtSignal(int)

    def __init__(self, parent=None, video=None):
        super().__init__(parent)
        self.__kill = False
        self.mutex = QMutex()

        self.video = video
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.resolution = self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.output_resolution = [640, 480]
        
        # play state
        self.number_of_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        self.current_frame = 0
        self.__is_playing = False
        self.__frame = None

        if video is None:
            raise Exception("Must provide a video")

    @property
    def playing(self):
        return self.__is_playing

    @property
    def frame(self):
        return self.__frame

    def run(self):
        self.mutex.lock()
        ret, self.__frame = self.video.read()
        self.mutex.unlock()
        self.render_frame()

        while not self.__kill:
            if self.playing:
                while ret and self.playing:
                    self.render_frame()

                    # Wait and get next frame
                    time.sleep(1/self.fps)

                    self.mutex.lock()
                    ret, self.__frame = self.video.read()
                    self.current_frame += 1

                    if (self.current_frame == self.number_of_frames):
                        self.pause()
                    self.mutex.unlock()
            else:
                time.sleep(1/self.fps) # do nothing

    def play(self):
        if self.playing:
            pass
        else:
            print("Thread playing")
            if self.current_frame >= self.number_of_frames:
                self.set_frame(0)
                
            self.__is_playing = True
            self.stateChanged.emit(self.playing)
            
    def pause(self):
        if not self.playing:
            pass
        else:
            print("Thread Pausing")
            self.__is_playing = False
            self.stateChanged.emit(self.playing)

    def render_frame(self):
        self.positionChanged.emit(self.current_frame)
        self.newFrame.emit(self.__frame)
        rgb = cv2.cvtColor(self.__frame, cv2.COLOR_BGR2RGB)

        # Convert into QT Format
        h, w, ch = rgb.shape
        bytesPerLine = ch*w
        qtImage = QImage(rgb, w, h, bytesPerLine, QImage.Format_RGB888)
        scaled = qtImage.scaled(self.output_resolution[0], self.output_resolution[1], Qt.KeepAspectRatio)
        self.changePixmap.emit(scaled) # emit event

    def set_frame(self, frame_index):
        if (0 <= frame_index < self.number_of_frames):
            self.mutex.lock()
            self.current_frame = frame_index
            self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, self.__frame = self.video.read()
            self.mutex.unlock()
            self.render_frame()
        else:
            raise Exception("index {} is out of the video bounds 0 -> {}".format(frame_index, self.number_of_frames))

    def updateSize(self, x, y):
        print("Updating output resolution to", x, y)
        self.output_resolution = [x, y]


class Video(QLabel):

    __sizeChanged = pyqtSignal(int, int)
    newFrame = pyqtSignal(numpy.ndarray) # Outputs an OpenCV frame before it is rendered to GUI
    positionChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None, video="./SampleVideo.mp4"):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        # Load Video
        self._video_path = video
        self.video = cv2.VideoCapture(video)
        atexit.register(self.video.release)
        self.__fps = self.video.get(cv2.CAP_PROP_FPS)
        self.__resolution = self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.__number_of_frames = self.video.get(cv2.CAP_PROP_FRAME_COUNT)
        print("Playing {} at {} fps and {}x{}".format(self._video_path, self.fps, self.resolution[0], self.resolution[1]))

        # Video Reader
        self.__image_update_thread = VideoThread(self, video=self.video)
        self.__image_update_thread.changePixmap.connect(self.__setImage)
        self.__image_update_thread.start()
        self.__sizeChanged.connect(self.__image_update_thread.updateSize)

        # Pass through signals
        self.__image_update_thread.newFrame.connect(self.newFrame.emit)
        self.__image_update_thread.positionChanged.connect(self.positionChanged.emit)
        self.__image_update_thread.stateChanged.connect(self.stateChanged.emit)

        self.setMinimumSize(1280, 640)

    @property
    def duration(self):
        return self.number_of_frames / self.fps

    @property
    def number_of_frames(self):
        return self.__number_of_frames

    @property
    def resolution(self):
        return self.__resolution

    @property
    def fps(self):
        return self.__fps

    @property
    def playing(self):
        return self.__image_update_thread.playing

    @property
    def position(self):
        return self.__image_update_thread.current_frame

    def __setImage(self, image):
        self.setPixmap(QPixmap.fromImage(image))

    def setFixedSize(self, x, y):
        super().setFixedSize(x, y)
        self.__sizeChanged.emit(x, y)

    def setMinimumSize(self, x, y):
        super().setMinimumSize(x, y)
        self.__sizeChanged.emit(x, y)

    def play(self):
        print("Playing")
        self.__image_update_thread.play()

    def pause(self):
        print("Pausing")
        self.__image_update_thread.pause()

    def setPosition(self, frame):
        print("Setting to", frame)
        self.__image_update_thread.set_frame(frame)





class VideoWidget(QWidget): #QDock

    def __init__(self, path=None):
        super().__init__()

        # Structure
        self.setLayout(QVBoxLayout())

        # Video
        self.videoContainer = QWidget()
        self.videoContainer.setLayout(QStackedLayout())
        self.video = Video(None, video=path)
        self.videoContainer.layout().addWidget(self.video)
        self.layout().addWidget(self.videoContainer)

        self.video.stateChanged.connect(self.__onPlayerStateChange)
        # self.video.durationChanged.connect(self.__onVideoDurationChange)
        self.video.setMinimumSize(640, 480)
        self.videoContainer.setMinimumSize(640, 480)

        # Buttons
        self.buttonRow = QWidget()
        self.buttonRowLayout = QHBoxLayout()
        self.buttonRow.setLayout(self.buttonRowLayout)
        self.layout().addWidget(self.buttonRow)
        # Play
        self.playButton = QPushButton()
        self.playButton.setText("Play")
        self.playButton.setEnabled(False)
        self.playButton.clicked.connect(self.play)
        self.buttonRowLayout.addWidget(self.playButton)
        # Progress Bar
        self.progressSlider = QSlider(Qt.Horizontal)
        self.progressSlider.setRange(0, self.video.number_of_frames)
        self.progressSlider.sliderMoved.connect(self.setPosition) # set position when user moves slider
        self.progressSlider.sliderPressed.connect(self.video.pause) # pause when user presses slider
        self.video.positionChanged.connect(self.progressSlider.setValue) # update the slider as video plays
        self.buttonRowLayout.addWidget(self.progressSlider)
        
        # Set Blurring variables
        self._blur_strands = []
        self._blur_object = None
        self._blur_layer = QLabel()
        self._blur_layer.setText("Hello There")
        self.videoContainer.layout().addWidget(self._blur_layer)
        self.videoContainer.layout().setCurrentWidget(self._blur_layer)
        self.videoContainer.layout().setStackingMode(QStackedLayout.StackAll)
        # TODO: when videoWidget size changes, update blur layer size

    @property
    def display_resolution(self):
        return self.video.size() # FIXME: get displayed video's resolution

    @property
    def video_resolution(self):
        return self.video.resolution


    @staticmethod
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
        
        if (instance is None): # spawn if no instance
            instance = VideoWidget(path=path)
        instance.playButton.setEnabled(True)
        return instance

    def play(self):
        ''' plays or pauses video '''
        if self.video.playing:
            self.video.pause()
        else:
            self.video.play()

    def __onPlayerStateChange(self, state):
        ''' changes the play/pause button depending on state '''
        if state:
            self.playButton.setText("Pause")
        else:
            self.playButton.setText("Play")

    def setPosition(self, pos):
        ''' Sets the current playback position of the video '''
        self.video.setPosition(pos)

    # def __onVideoDurationChange(self, duration):
    #     self.progressSlider.setRange(0, duration)


    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._blur_object = BlurStrand(self, self.display_resolution, self.video_resolution)
        self._blur_strands.append(self._blur_object)
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        # Get click location in movie's space
        self._blur_object.addPoint(
            self.video.position,
            (a0.localPos().x(), a0.localPos().y()),
            0.1, # TODO: Implement brush size
            self.display_resolution
        )
        return super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        print("Released", self._blur_object)
        self._blur_object = None
        return super().mouseReleaseEvent(a0)