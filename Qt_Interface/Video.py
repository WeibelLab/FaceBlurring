
from PyQt5 import QtGui
from PyQt5.QtCore import QDir, QEvent, QSize, QUrl, Qt, QThread, pyqtSignal, QMutex
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QDockWidget, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QStackedLayout, QWidget, QVBoxLayout, QProgressBar
from PyQt5.QtGui import QCursor, QFont, QImage, QPixmap

import cv2, os, shutil, atexit, numpy, time
from BlurObject import *
from Cursor import Cursor


class VideoThread(QThread):
    changePixmap = pyqtSignal(QImage)
    newFrame = pyqtSignal(int, numpy.ndarray)
    stateChanged = pyqtSignal(bool) # True for playing started. False for playing stopped
    positionChanged = pyqtSignal(int)

    def __init__(self, parent=None, video=None):
        super().__init__(parent)
        self.__kill = False
        self.mutex = QMutex()
        self.__exporter = None

        self.video = video
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        self.resolution = self.video.get(cv2.CAP_PROP_FRAME_WIDTH), self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.output_resolution = self.resolution
        
        # play state
        self.number_of_frames = int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        self.current_frame = 0
        self.__is_playing = False
        self.__is_exporting = False
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
            while not self.__kill and ret and self.playing and not self.__is_exporting:
                self.render_frame()

                # Wait and get next frame
                time.sleep(1/self.fps) # TODO: account for processing time

                if (self.current_frame >= self.number_of_frames-1):
                    self.pause()
                else: 
                    ret, frame = self.step()

            while not self.__kill and ret and self.__is_exporting:
                # print("Exporting Frame", self.current_frame, "of", self.number_of_frames-1)
                if (self.current_frame >= self.number_of_frames-1):
                    self.__is_exporting = False
                    self.__finishExport()
                    print("Export done no ret failure :)")
                    # break
                else:
                    ret, frame = self.step()
                    self.__export_progress_bar.setValue(self.current_frame)

                if not ret:
                    print("No return during export at frame {} / {}".format(self.current_frame-1, self.number_of_frames-1))
                    ret = True
                    self.__is_exporting = False
                    self.__finishExport()
                    print("Export done")
                    # break
            
            while not self.__kill and not self.playing and not self.__is_exporting:
                time.sleep(1/self.fps) # do nothing

    def __finishExport(self):
        print("Render loop closed")
        # Close writer and remove listeners
        self.__exporter.release()
        self.__exporter = None
        self.__is_exporting = False
        self.newFrame.disconnect(self.__exportFrame)
        print("Writer Closed")
        self.set_frame(self.__export_start_position)
        # remove progress bar
        self.__export_progress_bar.setValue(self.number_of_frames)
        self.__export_progress_bar.parent().layout().removeWidget(self.__export_progress_bar)
        self.__export_progress_bar.setParent(None)
        self.__export_progress_bar.deleteLater()

    def export(self, path, progressbar):
        print("Exporting to", path)

        # Get export information and video writer
        self.__export_start_position = self.current_frame
        resolution = tuple(map(int, self.resolution))
        self.__exporter = cv2.VideoWriter(
                path, 
                cv2.VideoWriter_fourcc(*"X264"),
                self.fps, 
                resolution)

        # Move video to beginning and listen for frames to export
        self.pause()
        self.newFrame.connect(self.__exportFrame)
        self.set_frame(0)
        self.positionChanged.emit(self.current_frame)

        # Create progress bar
        self.__export_progress_bar = progressbar
        self.__export_progress_bar.setMaximum(self.number_of_frames)
        self.__export_progress_bar.setValue(0)

        # Read first frame
        self.step()
        # self.render_frame()
        self.__is_exporting = True # causes thread to start exporting

    def __exportFrame(self, index, frame):
        if (self.__exporter != None):
            self.mutex.lock()
            self.__exporter.write(frame)
            self.mutex.unlock()


    def play(self):
        if self.playing:
            pass
        else:
            print("Thread playing")
            if self.current_frame >= self.number_of_frames-1:
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

    def step(self):
        self.mutex.lock()
        ret, self.__frame = self.video.read()
        self.mutex.unlock()

        self.current_frame += 1
        if ret:
            self.newFrame.emit(self.current_frame, self.__frame)
        
        return (ret, self.__frame)

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

    def reblit(self):
        self.set_frame(self.current_frame)

    def rerender(self):
        self.render_frame()

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

    def kill(self):
        self.__kill = True
        self.terminate()
        self.wait()


class Video(QLabel):

    __sizeChanged = pyqtSignal(int, int)
    newFrame = pyqtSignal(int, numpy.ndarray) # Outputs an OpenCV frame before it is rendered to GUI
    positionChanged = pyqtSignal(int)
    stateChanged = pyqtSignal(bool)

    
    # Click Events
    mouse_down = pyqtSignal(tuple)
    mouse_move = pyqtSignal(tuple)
    mouse_up = pyqtSignal(tuple)
    mouse_over = pyqtSignal(tuple)
    mouse_leave = pyqtSignal(tuple)
    scroll_event = pyqtSignal(int, float, float)

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

        # Click Events
        # self.mouse_down = pyqtSignal(Video, tuple)
        # self.mouse_move = pyqtSignal(Video, tuple)
        # self.mouse_up = pyqtSignal(Video, tuple)

        self.setFixedWidth(self.resolution[0]/2)

        # Blurring
        self._blur_strands = []
        self._blur_object = None

        # Set Cursor
        self.setCursor(Cursor())
        # self.setCursor(QCursor(Qt.CrossCursor))
        # cursor_size = self.cursor().pixmap().size()
        # self.cursor().pixmap().load("../assets/erase.png")
        # print("Cursor size",cursor_size.width(), cursor_size.height())
        self.installEventFilter(self)



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

    @property
    def frame(self):
        return self.__image_update_thread.frame

    def __setImage(self, image):
        self.setPixmap(QPixmap.fromImage(image))

    def export(self, path, progressbar):
        self.__image_update_thread.export(path, progressbar)

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
        self.__image_update_thread.set_frame(frame)

    def reblit(self):
        self.__image_update_thread.reblit()

    def rerender(self):
        self.__image_update_thread.rerender()



    def convert_point_to_video(self, x, y):
        '''
        Converts a point in the Video object PyQt space
        into the pixel in the video element
        '''

        new_x = numpy.interp(x, [0, self.size().width()], [0, self.resolution[0]])
        new_y = numpy.interp(y, [0, self.size().height()], [0, self.resolution[1]])
        return (new_x, new_y)

        

    def eventFilter(self, obj, event):
        if obj is self:
            if event.type() == QEvent.Enter:
                self.mouse_over.emit((event, self))
            elif event.type() == QEvent.Leave:
                self.mouse_leave.emit((event, self))

        return super(Video, self).eventFilter(obj, event)

    def wheelEvent(self, a0: QtGui.QWheelEvent) -> None:
        steps = a0.angleDelta().y() // 120
        self.scroll_event.emit(steps, a0.position().x(), a0.position().y())
        return super().wheelEvent(a0)

    def mousePressEvent(self, a0: QtGui.QMouseEvent) -> None:
        click = (a0.localPos().x(), a0.localPos().y())
        frame_loc = self.convert_point_to_video(*click)
        self.mouse_down.emit((self, frame_loc))
        return super().mousePressEvent(a0)

    def mouseMoveEvent(self, a0: QtGui.QMouseEvent) -> None:
        click = (a0.localPos().x(), a0.localPos().y())
        frame_loc = self.convert_point_to_video(*click)
        self.mouse_move.emit((self, frame_loc))
        return super().mouseMoveEvent(a0)

    def mouseReleaseEvent(self, a0: QtGui.QMouseEvent) -> None:
        click = (a0.localPos().x(), a0.localPos().y())
        frame_loc = self.convert_point_to_video(*click)
        self.mouse_up.emit((self, frame_loc))
        return super().mouseReleaseEvent(a0)

    def deleteLater(self) -> None:
        self.__image_update_thread.kill()
        return super().deleteLater()



class VideoWidget(QWidget): #QDock
    Widgets = []

    # Passthrough click events
    mouse_down = pyqtSignal(tuple)
    mouse_move = pyqtSignal(tuple)
    mouse_up = pyqtSignal(tuple)
    mouse_over = pyqtSignal(Video)
    mouse_leave = pyqtSignal(Video)
    scroll_event = pyqtSignal(Video, int, float, float)

    def __init__(self, name="Video", path=None, toolbar=None):
        super().__init__()
        # self.setFloating(False)
        # self.setFeatures(QDockWidget.DockWidgetMovable)
        # self.setAllowedAreas(Qt.AllDockWidgetAreas)

        # Structure
        self.setLayout(QVBoxLayout())
        self.setObjectName("VideoWidget")

        # Close button
        self.closeButton = QPushButton()
        self.closeButton.setText("X")
        self.closeButton.setEnabled(True)
        self.closeButton.clicked.connect(self.deleteLater)
        self.layout().addWidget(self.closeButton)
        
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
        self.progressSlider.setRange(0, int(self.video.number_of_frames-1))
        self.progressSlider.sliderMoved.connect(self.setPosition) # set position when user moves slider
        self.progressSlider.sliderPressed.connect(self.video.pause) # pause when user presses slider
        self.video.positionChanged.connect(self.progressSlider.setValue) # update the slider as video plays
        self.buttonRowLayout.addWidget(self.progressSlider)

        # Passthrough click events
        self.video.mouse_down.connect(self.mouse_down.emit)
        self.video.mouse_move.connect(self.mouse_move.emit)
        self.video.mouse_up.connect(self.mouse_up.emit)
        self.video.mouse_over.connect(lambda data: self.mouse_over.emit(data[1]))
        self.video.mouse_leave.connect(lambda data: self.mouse_leave.emit(data[1]))
        self.video.scroll_event.connect(lambda val, x, y: self.scroll_event.emit(self.video, val, x, y))

        # Register with Toolbar
        toolbar.register_video(self)
        VideoWidget.Widgets.append(self)
        self.destroyed.connect(lambda: VideoWidget.Widgets.remove(self)) # TODO: check if this works

    @property
    def display_resolution(self):
        return (self.video.size().width(), self.video.size().height())

    @property
    def video_resolution(self):
        return self.video.resolution

    def pause(self):
        self.video.pause()

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

    def reblit(self):
        self.video.reblit()

    def export(self, filename) :
        # QThread.thread()
        # threading.Thread(target=self.video.export, args=(filename, ))
        self.__export_progress_bar = QProgressBar()
        self.layout().addWidget(self.__export_progress_bar)
        self.__export_progress_bar.setGeometry(200, 80, 250, 20)
        self.video.export(filename, self.__export_progress_bar)


    # def __onVideoDurationChange(self, duration):
    #     self.progressSlider.setRange(0, duration)

    def deleteLater(self) -> None:
        print("Deleting")
        self.video.deleteLater()
        print("Deleted Video")
        return super().deleteLater()
