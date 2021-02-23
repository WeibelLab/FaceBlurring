from PyQt5.QtCore import QThread, QUrl, Qt, pyqtSignal
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtGui import QColor, QFont, QImage, QPixmap
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import *

import threading, atexit
import cv2, numpy, os, sys, shutil, time

app = QApplication([])
window = QWidget()
window.setLayout(QVBoxLayout())


class VideoThread(QThread):
    changePixmap = pyqtSignal(QImage)
    newFrame = pyqtSignal(numpy.ndarray)
    stateChanged = pyqtSignal(bool) # True for playing started. False for playing stopped
    frameIndexUpdated = pyqtSignal(int)

    def __init__(self, parent=None, video=None):
        super().__init__(parent)
        self.__kill = False

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
        
        ret, self.__frame = self.video.read()
        self.render_frame()

        while not self.__kill:
            if self.playing:
                while ret and self.playing:
                    self.render_frame()

                    # Wait and get next frame
                    time.sleep(1/self.fps)
                    ret, self.__frame = self.video.read()
                    self.current_frame += 1

                    if (self.current_frame == self.number_of_frames):
                        self.pause()
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
        self.frameIndexUpdated.emit(self.current_frame)
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
            self.current_frame = frame_index
            self.video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ret, self.__frame = self.video.read()
            self.render_frame()
        else:
            raise Exception("index {} is out of the video bounds 0 -> {}".format(frame_index, self.number_of_frames))

    def updateSize(self, x, y):
        print("Updating output resolution to", x, y)
        self.output_resolution = [x, y]


class Video(QLabel):

    __sizeChanged = pyqtSignal(int, int)
    newFrame = pyqtSignal(numpy.ndarray) # Outputs an OpenCV frame before it is rendered to GUI
    frameIndexChanged = pyqtSignal(int)
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
        self.__image_update_thread = VideoThread(window, video=self.video)
        self.__image_update_thread.changePixmap.connect(self.__setImage)
        self.__image_update_thread.start()
        self.__sizeChanged.connect(self.__image_update_thread.updateSize)
        self.__image_update_thread.newFrame.connect(self.newFrame.emit)
        self.__image_update_thread.frameIndexUpdated.connect(self.frameIndexChanged.emit)

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




    
stack = QWidget()
stack.setLayout(QStackedLayout())
stack.setMinimumSize(1000, 1000)
window.layout().addWidget(stack)

vid = Video()
# vid.play()
stack.layout().addWidget(vid)

font = QFont("Consolas", 120, QFont.Bold)
lab = QLabel()
stack.layout().addWidget(lab)
lab.setText("OVERLAY")
lab.setFont(font)
lab.setWindowFlags(Qt.FramelessWindowHint)
lab.setAttribute(Qt.WA_TranslucentBackground)

stack.layout().setStackingMode(QStackedLayout.StackAll)
stack.layout().setCurrentIndex(1)




# Button Row
button_row = QWidget()
button_row.setLayout(QHBoxLayout())
window.layout().addWidget(button_row)

play_button = QPushButton()
play_button.setText("play")
play_button.clicked.connect(vid.play)
button_row.layout().addWidget(play_button)

pause_button = QPushButton()
pause_button.setText("pause")
pause_button.clicked.connect(vid.pause)
button_row.layout().addWidget(pause_button)

slider = QSlider(Qt.Horizontal)
slider.setRange(0, vid.number_of_frames-1)
slider.setTickInterval(1)
slider.sliderMoved.connect(vid.setPosition)
slider.sliderPressed.connect(vid.pause)
vid.frameIndexChanged.connect(slider.setValue)
button_row.layout().addWidget(slider)


window.setMinimumSize(1000, 1000)

window.show()
app.exec_()