
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
    newFrame = pyqtSignal(int, numpy.ndarray)
    stateChanged = pyqtSignal(bool) # True for playing started. False for playing stopped
    positionChanged = pyqtSignal(int)

    def __init__(self, parent=None, video=None):
        super().__init__(parent)
        self.__kill = False
        self.mutex = QMutex()

        self.video = video
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.resolution = self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.output_resolution = self.resolution
        
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
        self.newFrame.emit(self.current_frame, self.__frame)
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
                    self.newFrame.emit(self.current_frame, self.__frame)
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
            self.newFrame.emit(self.current_frame, self.__frame)
            self.render_frame()
        else:
            raise Exception("index {} is out of the video bounds 0 -> {}".format(frame_index, self.number_of_frames))

    def updateSize(self, x, y):
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = x
        y = x/aspect_ratio
        self.output_resolution = [x, y]

        print("Request to update resolution of {} video ({} aspect ratio) to {} ({} aspect ratio).\n\tActually set to {}".format(
            self.resolution, aspect_ratio,
            (x, y), x/y,
            self.output_resolution
        ))

class Video(QLabel):

    __sizeChanged = pyqtSignal(int, int)
    newFrame = pyqtSignal(int, numpy.ndarray) # Outputs an OpenCV frame before it is rendered to GUI
    positionChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(bool)

    def __init__(self, parent=None, video="./SampleVideo.mp4"):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("border: #f00 solid 5px")

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
        self.__image_update_thread.newFrame.connect(self.newFrame.emit, type=Qt.DirectConnection)
        self.__image_update_thread.positionChanged.connect(self.positionChanged.emit)
        self.__image_update_thread.stateChanged.connect(self.stateChanged.emit)

        self.setFixedWidth(self.resolution[0]/2)

        # Blurring
        self._blur_strands = []
        self._blur_object = None

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
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = x
        y = x / aspect_ratio

        super().setFixedSize(x, y)
        self.__sizeChanged.emit(x, y)

    def setMinimumSize(self, x, y):
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = x
        y = x / aspect_ratio

        super().setMinimumSize(x, y)
        self.__sizeChanged.emit(x, y)

    def setFixedHeight(self, h: int) -> None:
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = h * aspect_ratio
        y = h
        self.setFixedSize(x, y)

    def setFixedWidth(self, w: int) -> None:
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = w
        y = w / aspect_ratio
        self.setFixedSize(x, y)

    def setMinimumHeight(self, minh: int) -> None:
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = minh * aspect_ratio
        y = minh
        self.setMinimumSize(x, y)

    def setMinimumWidth(self, minw: int) -> None:
        # Constrain size to video aspect ratio
        aspect_ratio = self.resolution[0] / self.resolution[1]
        x = minw
        y = minw / aspect_ratio
        self.setMinimumSize(x, y)

    def play(self):
        print("Playing")
        self.__image_update_thread.play()

    def pause(self):
        print("Pausing")
        self.__image_update_thread.pause()

    def setPosition(self, frame):
        print("Setting to", frame)
        self.__image_update_thread.set_frame(frame)



    def convert_point_to_video(self, x, y):
        '''
        Converts a point in the Video object PyQt space
        into the pixel in the video element
        '''

        new_x = numpy.interp(x, [0, self.size().width()], [0, self.resolution[0]])
        new_y = numpy.interp(y, [0, self.size().height()], [0, self.resolution[1]])
        return (new_x, new_y)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        click = (a0.localPos().x(), a0.localPos().y())
        frame_loc = self.convert_point_to_video(*click)
        print("Mouse clicked in Widget at {} in {} sized widget. Corresponding to {} in video of resolution {}".format(click, (self.size().width(), self.size().height()), frame_loc, self.resolution))

        self._blur_object = BlurStrand(self, self.resolution)
        self._blur_strands.append(self._blur_object)

        self.mouseMoveEvent(a0) # add starting point
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None: #FIXME: throwing error
        # Get click location in movie's space

        click = (a0.localPos().x(), a0.localPos().y())
        frame_loc = self.convert_point_to_video(*click)

        self._blur_object.addPoint(
            self.position,
            frame_loc,
            0.1, # TODO: Implement brush size
        )
        return super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        self._blur_object.complete()
        self.newFrame.connect(self._blur_object.checkBlurFrame, type=Qt.DirectConnection)
        print("Released", self._blur_object)
        self._blur_object = None
        return super().mouseReleaseEvent(a0)




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
        # self.video.setFixedWidth(640)

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
